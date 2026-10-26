"""Jellyfin Nfo 命名修复插件。

MoviePilot 刮削电影时生成的 NFO 文件名为 `<视频主体名>.nfo`（如「替身 (2020) - 1080p.nfo」），
而 Jellyfin 对电影的 NFO 读取以 `movie.nfo` 为最高优先级，导致 MoviePilot 写出的 NFO 不被
Jellyfin 读取，进而在 Jellyfin 中缺乏 tmdb id 等媒体身份，影响元数据关联与订阅去重。

本插件监听元数据刮削完成事件（MetadataScrape），在电影目录内将含 `<tmdbid>` 的 NFO 文件
复制为 `movie.nfo`，使 Jellyfin 能够正确读取。同时提供一次性全库补齐能力，用于修复存量电影。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger

# 电影媒体类型标识，兼容 MediaType 枚举与字符串值。
_MOVIE_TYPE_VALUES = {"电影", "movie", "MOVIE"}


def _is_movie_type(mtype: Any) -> bool:
    """判断媒体类型是否为电影。

    兼容 MediaType 枚举对象与字符串值。

    :param mtype: 媒体类型对象或字符串。
    :return: 是否为电影。
    """
    if mtype is None:
        return False
    value = getattr(mtype, "value", mtype)
    return str(value) in _MOVIE_TYPE_VALUES


def _has_tmdbid(nfo_path: Path) -> bool:
    """判断 NFO 文件内容是否包含 tmdbid 字段。

    :param nfo_path: NFO 文件路径。
    :return: 是否包含 tmdbid。
    """
    try:
        text = nfo_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "<tmdbid>" in text


class JellyfinNfoFixer(_PluginBase):
    """Jellyfin Nfo 命名修复插件。"""

    plugin_name = "Jellyfin Nfo命名修复"
    plugin_desc = "刮削完成后将电影目录内的 NFO 复制为 movie.nfo，修复 Jellyfin 无法读取 MoviePilot NFO 的问题。"
    plugin_icon = "jellyfinnfofixer.png"
    plugin_version = "1.0.0"
    plugin_label = "刮削"
    plugin_author = "local"
    author_url = None
    plugin_config_prefix = "jellyfinnfofixer_"
    plugin_order = 51
    auth_level = 1

    # 私有状态
    _enabled = False
    _movie_library_dirs: List[str] = []

    def init_plugin(self, config: Optional[Dict[str, Any]] = None) -> None:
        """根据插件配置初始化运行状态。

        :param config: 插件配置字典。
        """
        self._enabled = False
        self._movie_library_dirs = []
        if not config:
            return
        self._enabled = bool(config.get("enabled"))
        raw_dirs = config.get("movie_library_dirs", "")
        if raw_dirs:
            self._movie_library_dirs = [
                line.strip()
                for line in str(raw_dirs).splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。

        提供 /fix_nfo 命令，用于一次性全库补齐 movie.nfo。
        """
        return [
            {
                "cmd": "/fix_nfo",
                "event": EventType.PluginAction,
                "desc": "全库补齐 movie.nfo",
                "category": "刮削",
                "data": {
                    "action": "fix_nfo"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表。

        注册 /fix_nfo 与 /status 端点，供页面触发全库补齐与查看状态。
        """
        return [
            {
                "path": "/fix_nfo",
                "endpoint": self.api_fix_nfo,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "全库补齐 movie.nfo",
            },
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "查看当前状态",
            },
        ]

    def api_status(self) -> Dict[str, Any]:
        """返回插件运行状态摘要，供 Vue 详情页展示。

        :return: 包含启用状态与电影库目录列表的字典。
        """
        return {
            "success": True,
            "data": {
                "enabled": self._enabled,
                "movie_library_dirs": self._movie_library_dirs,
            },
        }

    def get_form(self) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """返回插件默认配置（Vue 模式下表单由远程 Config 组件渲染）。"""
        return [], {
            "enabled": False,
            "movie_library_dirs": "/media/电影"
        }

    def get_page(self) -> Optional[List[Dict[str, Any]]]:
        """返回插件详情页面（Vue 模式下由远程 Page 组件渲染）。"""
        return []
    def stop_service(self) -> None:
        """停止插件服务。"""
        return None

    @eventmanager.register(EventType.MetadataScrape)
    def on_metadata_scrape(self, event: Event) -> None:
        """监听元数据刮削完成事件，为电影目录生成 movie.nfo。

        :param event: 元数据刮削事件。
        """
        if not self._enabled:
            return
        event_data = event.event_data or {}
        if not event_data:
            return

        mediainfo = event_data.get("mediainfo")
        if not _is_movie_type(getattr(mediainfo, "type", None)):
            return

        fileitem = event_data.get("fileitem")
        item_path = getattr(fileitem, "path", None)
        if not item_path:
            return

        self._fix_movie_dir(Path(item_path))

    @eventmanager.register(EventType.PluginAction)
    def on_plugin_action(self, event: Event) -> None:
        """响应 /fix_nfo 命令，执行全库补齐。

        :param event: 插件动作事件。
        """
        if not self._enabled:
            return
        event_data = event.event_data or {}
        if event_data.get("action") != "fix_nfo":
            return

        user = event_data.get("user")
        channel = event_data.get("channel")
        try:
            result = self.fix_all()
            self.post_message(
                channel=channel,
                userid=user,
                title="Jellyfin Nfo命名修复",
                text=(
                    f"全库补齐完成：共 {result.get('total', 0)} 个电影目录，"
                    f"修复 {result.get('fixed', 0)}，跳过 {result.get('skipped', 0)}。"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Jellyfin Nfo命名修复：全库补齐异常：%s", exc)
            self.post_message(
                channel=channel,
                userid=user,
                title="Jellyfin Nfo命名修复",
                text=f"全库补齐失败：{exc}",
            )

    def _fix_movie_dir(self, item_path: Path) -> None:
        """为单个电影目录生成 movie.nfo。

        优先在目录内查找含 tmdbid 的 NFO 文件，复制为 movie.nfo。
        若传入的是文件路径，则取其父目录作为电影目录。

        :param item_path: 电影目录或电影文件路径。
        """
        movie_dir = item_path if item_path.is_dir() else item_path.parent
        if not movie_dir.is_dir():
            return

        source = self._find_tmdbid_nfo(movie_dir)
        if source is None:
            logger.debug("Jellyfin Nfo命名修复：目录内无含 tmdbid 的 NFO，跳过 %s", movie_dir)
            return

        target = movie_dir / "movie.nfo"
        try:
            if target.exists():
                existing = target.read_text(encoding="utf-8", errors="ignore")
                source_text = source.read_text(encoding="utf-8", errors="ignore")
                if existing == source_text:
                    return
            target.write_text(source.read_text(encoding="utf-8", errors="ignore"),
                              encoding="utf-8")
            logger.info("Jellyfin Nfo命名修复：已生成 movie.nfo：%s", target)
        except OSError as exc:  # noqa: BLE001
            logger.error("Jellyfin Nfo命名修复：写入 movie.nfo 失败 %s：%s", target, exc)

    @staticmethod
    def _find_tmdbid_nfo(movie_dir: Path) -> Optional[Path]:
        """在电影目录内查找含 tmdbid 的 NFO 文件。

        优先级：优先 `movie.nfo`（若其本身含 tmdbid），否则查找
        其余任意含 tmdbid 的 `.nfo` 文件（通常为 `<片名>.nfo`）。

        :param movie_dir: 电影目录。
        :return: 含 tmdbid 的 NFO 文件路径；未找到返回 None。
        """
        candidates = sorted(movie_dir.glob("*.nfo"), key=lambda p: p.name)
        for candidate in candidates:
            if candidate.name == "movie.nfo" and _has_tmdbid(candidate):
                return candidate
        for candidate in candidates:
            if _has_tmdbid(candidate):
                return candidate
        return None

    def fix_all(self) -> Dict[str, Any]:
        """一次性全库补齐 movie.nfo。

        遍历配置的电影库目录（含分类子目录下的电影目录），
        为每个电影目录生成 movie.nfo。

        :return: 处理结果统计。
        """
        total = 0
        fixed = 0
        skipped = 0
        for lib_dir in self._movie_library_dirs:
            root = Path(lib_dir)
            if not root.is_dir():
                logger.warning("Jellyfin Nfo命名修复：电影库目录不存在，跳过 %s", lib_dir)
                continue
            # 电影目录位于「分类/片名」两级或直接「片名」一级，
            # 这里遍历到含视频文件的目录即可。
            for movie_dir in self._iter_movie_dirs(root):
                total += 1
                source = self._find_tmdbid_nfo(movie_dir)
                if source is None:
                    skipped += 1
                    continue
                target = movie_dir / "movie.nfo"
                try:
                    target.write_text(
                        source.read_text(encoding="utf-8", errors="ignore"),
                        encoding="utf-8",
                    )
                    fixed += 1
                except OSError as exc:  # noqa: BLE001
                    logger.error("Jellyfin Nfo命名修复：写入失败 %s：%s", target, exc)
                    skipped += 1
        logger.info("Jellyfin Nfo命名修复：全库补齐完成，共 %d 个电影目录，修复 %d，跳过 %d",
                    total, fixed, skipped)
        return {"total": total, "fixed": fixed, "skipped": skipped}

    def api_fix_nfo(self) -> Dict[str, Any]:
        """处理 /fix_nfo API 请求，执行全库补齐。

        :return: 包含处理结果统计的响应字典。
        """
        if not self._enabled:
            return {"success": False, "message": "插件未启用"}
        result = self.fix_all()
        return {
            "success": True,
            "message": (
                f"全库补齐完成：共 {result.get('total', 0)} 个电影目录，"
                f"修复 {result.get('fixed', 0)}，跳过 {result.get('skipped', 0)}。"
            ),
            "data": result,
        }

    @staticmethod
    def _iter_movie_dirs(root: Path):
        """遍历电影库根目录下的所有电影目录。

        电影目录判定：目录内包含视频文件（mkv/mp4/avi/ts/iso 等），
        或包含含 tmdbid 的 NFO 文件。

        :param root: 电影库根目录。
        :return: 电影目录的生成器。
        """
        video_exts = {".mkv", ".mp4", ".avi", ".ts", ".m2ts", ".iso", ".wmv", ".mov", ".rmvb"}
        for entry in sorted(root.rglob("*")):
            if not entry.is_dir():
                continue
            # 跳过 trickplay 等元数据子目录
            if "trickplay" in entry.name.lower():
                continue
            has_video = any(
                child.is_file() and child.suffix.lower() in video_exts
                for child in entry.iterdir()
            )
            if has_video:
                yield entry


__all__ = ["JellyfinNfoFixer"]
