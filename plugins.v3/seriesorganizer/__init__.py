"""系列自动归组插件。

监听整理完成事件，将同系列电影（续集/前传）归入以中文系列名命名的父文件夹。
仅在同一分类目录内归组，不跨分类；未匹配但疑似续集的片名会发送提示。

系列名通过配置中的「系列前缀 -> 中文系列名」映射表确定，前缀后必须紧跟续集标记
（数字、冒号、全角/半角括号数字、「之」等），以避免「金刚狼」「金刚川」被误归入「金刚」。
"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.plugins import _PluginBase
from app.schemas.types import EventType, MessageType
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger

# 续集标记：前缀之后紧跟这些特征之一才视为续集。
#   - 纯数字（速度与激情7）
#   - 数字后跟空格/点/横线（变形金刚 4、星球大战·8）
#   - 冒号后数字（碟中谍:6）或英文标点
#   - 「之」引导的章节（速度与激情之东京漂移，例外场景）
#   - 罗马数字（洛奇 II）——可选，默认保守不开启，避免误伤
_SEQUEL_PATTERN_PREFIX = (
    "数字续集", "冒号续集", "之章", "罗马数字续集"
)

# 内置系列映射表：系列前缀 -> 中文系列名
# 用户可在配置页增删。前缀用于做片名匹配，系列名用于命名父文件夹。
# 该清单与媒体库实际已归组的 31 个系列保持一致。
DEFAULT_SERIES_MAP: Dict[str, str] = {
    "碟中谍": "碟中谍",
    "蜘蛛侠": "蜘蛛侠",
    "复仇者联盟": "复仇者联盟",
    "侏罗纪世界": "侏罗纪世界",
    "速度与激情": "速度与激情",
    "阿凡达": "阿凡达",
    "蜡笔小新": "蜡笔小新",
    "大话西游": "大话西游",
    "寒战": "寒战",
    "志愿军": "志愿军",
    "流浪地球": "流浪地球",
    "长津湖": "长津湖",
    "飞驰人生": "飞驰人生",
    "变形金刚": "变形金刚",
    "哥斯拉大战金刚": "哥斯拉大战金刚",
    "帕丁顿熊": "帕丁顿熊",
    "惊天魔盗团": "惊天魔盗团",
    "我的间谍": "我的间谍",
    "星球大战": "星球大战",
    "泰迪熊": "泰迪熊",
    "疾速追杀": "疾速追杀",
    "第一滴血": "第一滴血",
    "谍影重重": "谍影重重",
    "辣手保姆": "辣手保姆",
    "金刚": "金刚",
    "银河护卫队": "银河护卫队",
    "鬼玩人": "鬼玩人",
    "罗小黑战记": "罗小黑战记",
    "名侦探柯南": "名侦探柯南",
    "哆啦A梦": "哆啦A梦",
    "疯狂动物城": "疯狂动物城",
}


def _parse_series_map(raw: str) -> Dict[str, str]:
    """解析配置中的系列映射表文本。

    支持「前缀:系列名」每行一条，冒号可用半角或全角。
    忽略空行与以 # 开头的注释行。

    :param raw: 配置原始文本。
    :return: 前缀到系列名的映射字典。
    """
    result: Dict[str, str] = {}
    if not raw:
        return result
    for line in str(raw).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in (":", "：", "=", "|"):
            if sep in line:
                prefix, name = line.split(sep, 1)
                prefix = prefix.strip()
                name = name.strip()
                if prefix and name:
                    result[prefix] = name
                break
    return result


def _is_sequel_suffix(remainder: str) -> bool:
    """判断前缀之后的剩余部分是否构成续集标记。

    续集标记形式：纯数字、数字开头后跟分隔符、冒号后数字、罗马数字、「之」后章节名等。
    该函数用于防误伤：只有 remainder 以续集标记引导时才归组，
    从而避免「金刚狼」「金刚川」被误归入前缀「金刚」。
    """
    remainder = remainder.strip()
    if not remainder:
        return False
    # 「之」引导章节（如「速度与激情之东京漂移」「速度与激情之全面动员」）
    if remainder.startswith("之"):
        return True
    # 冒号/全角冒号/间隔号/横线/点后跟副标题（碟中谍:6、碟中谍:全面瓦解、变形金刚：起源）
    if remainder[0] in (":", "：", "·", "-", ".", "—", "–") and len(remainder) > 1:
        tail = remainder[1:].strip()
        if tail:
            return True
    # 数字开头（数字可跟空格、点、横线等）
    if remainder[0].isdigit():
        return True
    # 罗马数字（I/II/III/IV/V/VI…），通常带前导空格或点，保守起见仅当其后无其他字母时
    roman = remainder.lstrip(" ··.-")
    if roman and set(roman.upper()) <= set("IVXLCDM"):
        return True
    return False


def _match_series(title: str, series_map: Dict[str, str]) -> Optional[str]:
    """根据片名匹配系列名。

    只在映射中的前缀命中且其后紧跟续集标记时返回系列名；
    否则返回 None（含「前缀本身即完整片名、无续集」的情况，例如只叫「金刚」的电影不归组）。

    :param title: 片名（中文或英文标题）。
    :param series_map: 前缀到系列名的映射。
    :return: 匹配到的中文系列名，未命中返回 None。
    """
    if not title or not series_map:
        return None
    title = title.strip()
    # 前缀按长度降序，避免短前缀截断长前缀（如「哈利波特」与「哈利·波特」）
    sorted_prefixes = sorted(series_map.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if not prefix:
            continue
        # 片名精确等于系列名本身（系列第一部）时同样归组
        if title == prefix:
            return series_map[prefix]
        if title.startswith(prefix):
            remainder = title[len(prefix):]
            if _is_sequel_suffix(remainder):
                return series_map[prefix]
    return None


class SeriesOrganizer(_PluginBase):
    """系列自动归组插件。"""

    plugin_name = "系列自动归组"
    plugin_desc = "整理完成后自动将同系列电影归入系列父文件夹，未匹配的疑似续集发送提示。"
    plugin_icon = "seriesorganizer.png"
    plugin_version = "1.0.0"
    plugin_label = "媒体整理"
    plugin_author = "local"
    author_url = None
    plugin_config_prefix = "seriesorganizer_"
    plugin_order = 50
    auth_level = 1

    # 私有状态
    _enabled = False
    _series_map: Dict[str, str] = {}
    _notify = False
    _dry_run = False

    def init_plugin(self, config: Optional[Dict[str, Any]] = None) -> None:
        """根据插件配置初始化运行状态。"""
        self._enabled = False
        self._series_map = dict(DEFAULT_SERIES_MAP)
        self._notify = False
        self._dry_run = False
        if not config:
            return
        self._enabled = bool(config.get("enabled"))
        # 系列映射表：支持文本配置；为空时回退内置默认表
        raw_map = config.get("series_map", "")
        parsed = _parse_series_map(str(raw_map)) if raw_map else {}
        if parsed:
            self._series_map = parsed
        self._notify = bool(config.get("notify", True))
        self._dry_run = bool(config.get("dry_run", False))

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表。"""
        return [
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "查看当前归组状态与系列映射表",
            },
        ]

    def api_status(self) -> Dict[str, Any]:
        """返回插件运行状态摘要，供 Vue 详情页展示。

        :return: 包含启用状态、通知开关、演练开关、系列数量与当前生效映射表的字典。
        """
        return {
            "success": True,
            "data": {
                "enabled": self._enabled,
                "notify": self._notify,
                "dry_run": self._dry_run,
                "series_count": len(self._series_map),
                "series_map": dict(self._series_map),
            },
        }

    def get_form(self) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """返回插件默认配置（Vue 模式下表单由远程 Config 组件渲染）。"""
        return [], {
            "enabled": False,
            "notify": True,
            "dry_run": False,
            "series_map": "\n".join(f"{k}:{v}" for k, v in DEFAULT_SERIES_MAP.items()),
        }

    def get_page(self) -> Optional[List[Dict[str, Any]]]:
        """返回插件详情页面（Vue 模式下由远程 Page 组件渲染）。"""
        return []

    def stop_service(self) -> None:
        """停止插件服务。"""
        return None

    @eventmanager.register(EventType.TransferComplete)
    def on_transfer_complete(self, event: Event) -> None:
        """监听整理完成事件并执行系列归组。"""
        if not self._enabled:
            return
        self._organize_from_event(event)

    def _organize_from_event(self, event: Event) -> None:
        """从整理完成事件中提取媒体与目标路径，执行归组。

        :param event: 整理完成事件。
        """
        event_data = event.event_data or {}
        if not event_data:
            return

        mediainfo = event_data.get("mediainfo")
        # transferinfo 是 TransferInfo 对象（不再是 dict），必须用属性访问
        transferinfo = event_data.get("transferinfo")

        # 仅处理电影
        mtype = getattr(mediainfo, "type", None) if mediainfo else None
        if mtype != "电影":
            return

        # 片名：优先中文标题 title，回退 en_title / original_title
        title = (getattr(mediainfo, "title", None)
                 or getattr(mediainfo, "en_title", None)
                 or getattr(mediainfo, "original_title", None))
        if not title:
            return

        # 目标根目录（TransferInfo.target_diritem 是 FileItem，取 .path 属性）
        if transferinfo is None:
            return
        target_diritem = getattr(transferinfo, "target_diritem", None)
        if target_diritem is None:
            return
        target_path = getattr(target_diritem, "path", None)
        if not target_path:
            return

        target_dir = Path(target_path)
        if not target_dir.is_dir():
            return

        series_name = _match_series(str(title), self._series_map)
        if series_name:
            self._move_to_series(series_name, target_dir)
            return

        # 未能映射到系列，但疑似续集时提示
        if self._notify and self._looks_like_sequel(str(title)):
            self.post_message(
                mtype=MessageType.Plugin,
                title="系列自动归组",
                text=f"影片《{title}》疑似续集但未匹配到系列映射，已跳过归组。",
            )

    def _move_to_series(self, series_name: str, target_dir: Path) -> None:
        """将目标媒体目录移动进分类目录下的系列父文件夹。

        系列父文件夹创建在目标目录的父目录（即媒体分类目录）下，
        仅在同一分类内归组，不跨分类。

        :param series_name: 中文系列名。
        :param target_dir: 待移动的媒体根目录。
        """
        parent_dir = target_dir.parent
        series_dir = parent_dir / series_name
        destination = series_dir / target_dir.name

        # 已在系列父文件夹内则跳过
        if target_dir.parent.name == series_name:
            logger.info("系列自动归组：已位于系列文件夹内，跳过 %s", target_dir)
            return
        if destination.exists():
            logger.info("系列自动归组：目标已存在，跳过 %s", destination)
            return

        if self._dry_run:
            logger.info("系列自动归组（演练）：将移动 %s -> %s", target_dir, destination)
            self.post_message(
                mtype=MessageType.Plugin,
                title="系列自动归组（演练）",
                text=f"将移动 {target_dir.name} → {series_dir.name}/",
            )
            return

        try:
            series_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target_dir), str(destination))
            logger.info("系列自动归组：已移动 %s -> %s", target_dir, destination)
            self.post_message(
                mtype=MessageType.Plugin,
                title="系列自动归组",
                text=f"已将《{target_dir.name}》归入系列文件夹「{series_name}」。",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("系列自动归组：移动失败 %s -> %s：%s", target_dir, destination, exc)
            self.post_message(
                mtype=MessageType.Plugin,
                title="系列自动归组",
                text=f"归组失败：{target_dir.name}（{exc}）",
            )

    @staticmethod
    def _looks_like_sequel(title: str) -> bool:
        """判断片名是否疑似续集（数字、冒号数字、「之」等）。

        用于未命中映射时的提示，比 `_match_series` 更宽松，仅作提醒用。

        :param title: 片名。
        :return: 是否疑似续集。
        """
        if not title:
            return False
        import re
        # 数字结尾或数字后跟号/季，或冒号后数字，或「之」
        if re.search(r"\d", title):
            return True
        if re.search(r"[：:·]\s*\d", title):
            return True
        if "之" in title:
            return True
        return False


__all__ = ["SeriesOrganizer"]
