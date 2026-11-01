"""订阅入库自停核心扫描逻辑。

遍历「订阅中(R)」的订阅，逐个判定媒体是否已完整入库，命中则暂停或删除。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.chain.base import ChainBase
from app.db.oper.subscribe import SubscribeOper
from app.schemas.context import MediaInfo
from app.schemas.types import MediaType
from app.sdk.logging import logger


@dataclass
class ScanHit:
    """单条命中记录。"""

    subscribe_id: int
    name: str
    media_source: Optional[str]
    media_id: Optional[str]
    mtype: Optional[str]
    season: Optional[int]
    action: str
    reason: str


@dataclass
class ScanReport:
    """一次扫描的完整报告。"""

    scanned_count: int = 0
    hits: List[ScanHit] = field(default_factory=list)
    processed_count: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def hit_count(self) -> int:
        """命中并成功处理的订阅数。

        :return: 处理成功的命中数。
        """
        return self.processed_count

    def to_dict(self) -> Dict[str, Any]:
        """将报告序列化为可 JSON 化的字典。

        :return: 报告字典。
        """
        return {
            "scanned_count": self.scanned_count,
            "hit_count": self.processed_count,
            "processed_count": self.processed_count,
            "hits": [
                {
                    "subscribe_id": h.subscribe_id,
                    "name": h.name,
                    "season": h.season,
                    "action": h.action,
                    "reason": h.reason,
                }
                for h in self.hits
            ],
            "errors": self.errors,
        }


class SubscriptionAutoStopScanner:
    """订阅入库自停扫描器。"""

    def __init__(
        self,
        subscribe_oper: SubscribeOper,
        media_chain: ChainBase,
        action: str = "pause",
    ):
        """初始化扫描器。

        :param subscribe_oper: 订阅数据操作对象。
        :param media_chain: 用于库存在判断的链基类。
        :param action: 命中后的动作，pause 或 delete。
        """
        self._subscribe_oper = subscribe_oper
        self._media_chain = media_chain
        self._action = action

    def run(self) -> ScanReport:
        """执行完整扫描。

        :return: 扫描报告。
        """
        report = ScanReport()
        try:
            subscriptions = self._subscribe_oper.list(state="R")
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"拉取订阅失败: {exc}")
            logger.error(f"订阅入库自停：拉取订阅失败: {exc}")
            return report

        report.scanned_count = len(subscriptions)
        for sub in subscriptions:
            try:
                if not self._should_stop(sub):
                    continue
                hit = self._apply(sub)
                report.hits.append(hit)
                report.processed_count += 1
            except Exception as exc:  # noqa: BLE001
                name = getattr(sub, "name", "未知")
                report.errors.append(f"{name}: {exc}")
                logger.error(f"订阅入库自停：处理订阅 {name} 失败: {exc}")
        return report

    def _should_stop(self, sub) -> bool:
        """判断单条订阅是否已完整入库。

        :param sub: 订阅对象。
        :return: 是否命中。
        """
        media_source = getattr(sub, "media_source", None)
        media_id = getattr(sub, "media_id", None)
        mtype = getattr(sub, "type", None)

        # 豆瓣等非 TMDB 源直接无法用 media_exists 定位，跳过避免误判。
        if not media_id or media_source != "themoviedb":
            return False

        media_info = MediaInfo(
            media_source=media_source,
            media_id=str(media_id),
            type=mtype,
            season=getattr(sub, "season", None),
            year=getattr(sub, "year", None),
        )

        exists = self._media_chain.media_exists(mediainfo=media_info)
        if exists is None:
            return False

        # 电影：存在即命中。
        if mtype != MediaType.TV.value:
            return True

        # 电视剧：目标季整季全齐才命中。
        return self._tv_season_complete(sub, exists.seasons or {})

    def _tv_season_complete(self, sub, exist_seasons: Dict[int, List[int]]) -> bool:
        """判断电视剧目标季是否整季全齐。

        :param sub: 订阅对象。
        :param exist_seasons: 媒体服务器返回的已存在集（按季归组）。
        :return: 目标季是否集齐。
        """
        season = getattr(sub, "season", None)
        total = getattr(sub, "total_episode", None)
        # 未标记季号或未填总集数时不判定，避免误停。
        if season is None or not total or total <= 0:
            return False
        existing = exist_seasons.get(season, [])
        return len(existing) >= total

    def _apply(self, sub) -> ScanHit:
        """对命中订阅执行动作。

        :param sub: 订阅对象。
        :return: 命中记录。
        """
        sid = getattr(sub, "id", None)
        name = getattr(sub, "name", "未知")
        season = getattr(sub, "season", None)

        if self._action == "delete":
            self._subscribe_oper.delete(sid)
            reason = "已完整入库，自动删除订阅"
        else:
            self._subscribe_oper.update(sid, {"state": "S"})
            reason = "已完整入库，自动暂停订阅"

        logger.info("订阅入库自停：%s -> %s", name, reason)
        return ScanHit(
            subscribe_id=sid,
            name=name,
            media_source=getattr(sub, "media_source", None),
            media_id=getattr(sub, "media_id", None),
            mtype=getattr(sub, "type", None),
            season=season,
            action=self._action,
            reason=reason,
        )
