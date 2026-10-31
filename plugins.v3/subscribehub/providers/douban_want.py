"""豆瓣想看来源：解析用户个人「想看」RSS，产出标准化条目。

数据来源为豆瓣个人动态 RSS（``https://www.douban.com/feed/people/{用户ID}/interests``），
抓取逻辑移植自参考插件 ``doubansync``（豆瓣想看），收敛为 ``RankProvider`` 后由统一落地管线消费。

与「豆瓣榜单」（providers/douban.py，抓公开榜单）的区别：本来源抓取的是**单个豆瓣用户**
自己标记的「想看」清单，属于个性化订阅，而非大众榜单。识别与加订阅统一交给 executor，
本模块只负责「抓取 → 提取 douban_id → 产出 RankMediaItem」。
"""
from __future__ import annotations

import datetime
from typing import Iterator, List, Optional

from app.schemas.types import MediaSource
from app.sdk.config import settings
from app.sdk.logging import logger
from app.sdk.network import RssHelper

from ..core.models import FieldSpec, ProviderSpec, RankMediaItem
from ..core.provider import ProviderContext, RankProvider
from ..core.registry import register

# 豆瓣个人「想看」RSS 模板，%s 为豆瓣用户 ID。
_INTERESTS_URL = "https://www.douban.com/feed/people/%s/interests"

# 默认同步天数（只处理最近 N 天内标记的「想看」）。
_DEFAULT_DAYS = 7

# 默认执行周期：每天上午 8 点。
_DEFAULT_CRON = "0 8 * * *"

# RSS 中「想看」条目的类型前缀（title 前 2 字符）。
_WANT_PREFIX = "想看"


@register
class DoubanWantProvider(RankProvider):
    """豆瓣想看来源：解析个人「想看」RSS 为标准化 ``RankMediaItem``。"""

    provider_id = "douban_want"
    provider_name = "豆瓣想看"

    # 本来源支持「搜索下载优先」：识别后先搜资源直接下载，失败再回退加订阅。
    supports_search_download = True

    def get_spec(self) -> ProviderSpec:
        """返回本来源的元描述（选项 schema）。"""
        return ProviderSpec(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            default_cron=_DEFAULT_CRON,
            options_schema=[
                FieldSpec(
                    key="users",
                    label="豆瓣用户ID",
                    kind="text",
                    default="",
                    hint="要同步「想看」的豆瓣用户 ID，多个用英文逗号分隔（形如 https://www.douban.com/people/123456789/ 中的数字）",
                ),
                FieldSpec(
                    key="days",
                    label="同步天数",
                    kind="number",
                    default=_DEFAULT_DAYS,
                    hint="只处理最近 N 天内标记的「想看」",
                ),
                FieldSpec(
                    key="search_download",
                    label="搜索下载优先",
                    kind="switch",
                    default=False,
                    hint="开启后，媒体库缺失时先搜索资源直接下载，下载失败/无资源再回退为订阅",
                ),
            ],
            filters_schema=[],
            notice="同步的是豆瓣用户个人的「想看」清单，不是公开榜单。需填写正确的豆瓣用户 ID；"
                   "豆瓣个人 RSS 无需登录即可读取「想看」动态。",
        )

    def has_listening(self, options: dict) -> bool:
        """配置了至少一个非空豆瓣用户 ID，即认为有可监听内容。"""
        options = options or {}
        return bool(self._as_user_list(options.get("users")))

    def fetch(self, options: dict, context: ProviderContext) -> Iterator[RankMediaItem]:
        """抓取多个用户的个人「想看」RSS，逐条产出 ``RankMediaItem``。

        单条 entry 解析失败内部 try/except continue；整源请求失败向上抛出由 runner 捕获。
        """
        options = options or {}
        user_ids = self._as_user_list(options.get("users"))
        days = self._to_int(options.get("days"), _DEFAULT_DAYS)
        for user_id in user_ids:
            yield from self._fetch_user(user_id, days)

    def _fetch_user(self, user_id: str, days: int) -> Iterator[RankMediaItem]:
        """抓取单个用户的「想看」RSS，逐条产出条目。"""
        url = _INTERESTS_URL % user_id
        logger.info(f"{self.provider_name}：开始同步用户 {user_id} 的豆瓣想看数据 ...")
        results = RssHelper().parse(url, headers={"User-Agent": settings.USER_AGENT})
        if not results:
            logger.warning(f"{self.provider_name}：未获取到用户 {user_id} 豆瓣RSS数据：{url}")
            return
        logger.info(f"{self.provider_name}：获取到用户 {user_id} 豆瓣RSS数据 {len(results)} 条")
        for result in results:
            try:
                media_item = self._parse_entry(result, user_id, days)
            except Exception as err:  # noqa: BLE001 - 单条解析失败不影响其余条目
                logger.error(f"{self.provider_name}：解析豆瓣想看条目失败：{err}")
                continue
            if media_item is not None:
                yield media_item

    def _parse_entry(self, result: dict, user_id: str, days: int) -> Optional[RankMediaItem]:
        """将单条 RSS entry 解析为 ``RankMediaItem``（非「想看」/超期/无链接返回 None）。"""
        # 标题前 2 字符是「想看」。豆瓣 RSS 的 title 形如「想看」+ 电影名。
        raw_title = str(result.get("title") or "")
        dtype = raw_title[:2]
        title = raw_title[2:]
        if dtype != _WANT_PREFIX:
            logger.info(f"{self.provider_name}：标题「{title}」非想看数据，跳过")
            return None
        link = result.get("link")
        if not link:
            logger.warning(f"{self.provider_name}：标题「{title}」未获取到链接，跳过")
            return None

        # 天数过滤：只处理最近 N 天内标记的「想看」。
        pubdate = result.get("pubdate")
        if pubdate is not None:
            try:
                elapsed_days = (datetime.datetime.now(datetime.timezone.utc) - pubdate).days
                if elapsed_days > int(days):
                    logger.info(f"{self.provider_name}：标题「{title}」已超过同步天数，跳过（{pubdate}）")
                    return None
            except (TypeError, ValueError):
                # pubdate 格式异常时不阻断，继续处理。
                pass

        # douban_id：链接形如 https://movie.douban.com/subject/1234567/，取倒数第二段。
        douban_id = str(link).split("/")[-2]
        if not douban_id or not douban_id.isdigit():
            logger.warning(f"{self.provider_name}：标题「{title}」未能提取豆瓣ID，跳过：{link}")
            return None

        nickname = str(result.get("nickname") or "")
        return RankMediaItem(
            title=title,
            year=None,
            type_hint=None,
            douban_id=douban_id,
            media_source=MediaSource.Douban,
            media_id=douban_id,
            poster=None,
            source_meta={"link": str(link), "user_id": user_id, "nickname": nickname},
            unique_seed=f"{user_id}:{douban_id}",
        )

    # ------------------------------------------------------------------ #
    # 工具函数
    # ------------------------------------------------------------------ #
    @staticmethod
    def _as_user_list(value) -> List[str]:
        """把用户 ID 配置统一成字符串列表（兼容逗号分隔字符串/列表）。"""
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return []

    @staticmethod
    def _to_int(value, default: int) -> int:
        """安全转 int，失败回退默认。"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
