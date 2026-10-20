"""ThePornDB 成人元数据刮削插件。

在 MoviePilot 端对指定媒体库目录（通常为成人内容库）进行刮削：
遍历库根目录下的各分类子目录，识别每个条目目录名，智能探测其属于
ThePornDB 的 Scene（欧美场景）、JAV（番号）还是 Movie（成片），
调用 ThePornDB REST API 获取元数据，将元数据写成 Kodi/NFO 格式的
``movie.nfo`` 落盘到条目目录，并下载海报保存为 ``poster.jpg``。

Jellyfin 侧保持只读：本插件把 NFO 与海报写到媒体库目录，Jellyfin 扫描
即可读取，不再由 Jellyfin 侧刮削。
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.plugins import _PluginBase
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger
from app.schemas.types import EventType

# ThePornDB REST API 根地址。
_TPDB_API = "https://api.theporndb.net"
# 单次请求的默认每页条数。
_PER_PAGE = 5
# 相邻两次请求的最小间隔（秒），用于温和限速，避免触发限流。
_REQUEST_MIN_INTERVAL = 0.5
# 上次请求的时间戳（模块级，用于串行限速）。
_last_request_ts = 0.0
# 后台海报下载线程池（模块级，异步下载不阻塞主刮削流程）。
_poster_executor: Optional[ThreadPoolExecutor] = None


def _get_poster_executor() -> ThreadPoolExecutor:
    """获取（并按需创建）后台海报下载线程池。

    :return: 全局海报下载线程池。
    """
    global _poster_executor
    if _poster_executor is None:
        _poster_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tpdb-poster")
    return _poster_executor
# 视频文件扩展名，用于判断目录内是否存在视频。
_VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".ts", ".m2ts", ".iso", ".wmv",
               ".mov", ".rmvb", ".flv", ".m4v", ".webm", ".mpg", ".mpeg"}
# JAV 番号形如 ABC-123、ABC 123、ABC123、1ABC-123 等（连字符或空格均可作分隔）。
_JAV_RE = re.compile(
    r"(?<![A-Z0-9])[A-Z]{2,6}\s?-?\s?\d{2,5}(?![A-Z0-9])", re.IGNORECASE)
# 命名中明显指向 JAV 的关键词/番号前缀。
_JAV_HINTS = ("jav", "snis", "ssni", "ipx", "ipz", "mide", "abp", "pppd",
              "rbd", "shkd", "ssis", "star", "fc2", "heyzo", "carib",
              "atid", "cesd", "gas", "hdd", "hhd", "tikc", "pkpt", "mxgs",
              "nhdtb", "dtt")


def _is_video(entry: Path) -> bool:
    """判断路径是否为视频文件。"""
    return entry.is_file() and entry.suffix.lower() in _VIDEO_EXTS


def _xml_escape(text: str) -> str:
    """转义 XML 特殊字符。"""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))


class TpdbScraper(_PluginBase):
    """ThePornDB 成人元数据刮削插件。"""

    plugin_name = "ThePornDB 成人刮削"
    plugin_desc = "在 MoviePilot 端对成人内容库调用 ThePornDB 刮削元数据，NFO 落盘并下载海报。"
    plugin_icon = "tpdbscraper.png"
    plugin_version = "1.0.0"
    plugin_label = "刮削,成人"
    plugin_author = "local"
    plugin_config_prefix = "tpdbscraper_"
    plugin_order = 50
    auth_level = 1

    # 私有运行状态
    _enabled = False
    _api_token = ""
    _library_dirs: List[str] = []
    _overwrite_nfo = False
    _download_poster = True
    _interval_minutes = 10
    _batch_size = 50
    _stashdb_enabled = False
    _stashdb_api_key = ""

    def init_plugin(self, config: Optional[Dict[str, Any]] = None) -> None:
        """根据插件配置初始化运行状态。"""
        self.stop_service()
        self._enabled = False
        self._api_token = ""
        self._library_dirs = []
        self._overwrite_nfo = False
        self._download_poster = True
        self._interval_minutes = 10
        self._batch_size = 50
        self._stashdb_enabled = False
        self._stashdb_api_key = ""
        if not config:
            return
        self._enabled = bool(config.get("enabled"))
        self._api_token = str(config.get("api_token") or "").strip()
        raw_dirs = config.get("library_dirs") or ""
        if raw_dirs:
            self._library_dirs = [
                line.strip()
                for line in str(raw_dirs).splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        self._overwrite_nfo = bool(config.get("overwrite_nfo"))
        self._download_poster = bool(config.get("download_poster", True))
        self._stashdb_enabled = bool(config.get("stashdb_enabled"))
        self._stashdb_api_key = str(config.get("stashdb_api_key") or "").strip()
        try:
            self._interval_minutes = int(config.get("interval_minutes") or 10)
        except (TypeError, ValueError):
            self._interval_minutes = 10
        try:
            self._batch_size = int(config.get("batch_size") or 50)
        except (TypeError, ValueError):
            self._batch_size = 50

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件渲染模式。

        当前使用 Vuetify JSON 配置（无需前端联邦构建产物）；
        前端联邦源码保留在插件目录，待有 Node 构建环境后再切换为 vue 模式。
        """
        return "vuetify", None

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。"""
        return [
            {
                "cmd": "/tpdb_scrape",
                "event": EventType.PluginAction,
                "desc": "全库刮削 ThePornDB 元数据",
                "category": "刮削",
                "data": {"action": "tpdb_scrape"},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表。"""
        return [
            {
                "path": "/scrape_now",
                "endpoint": self.api_scrape_now,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即刮削全库",
            },
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "查看刮削统计",
            },
        ]

    def get_form(self) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """返回插件配置表单与默认配置。"""
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VSwitch",
                        "props": {"model": "enabled", "label": "启用插件"},
                    },
                    {
                        "component": "VTextField",
                        "props": {
                            "model": "api_token",
                            "label": "ThePornDB API Token",
                            "placeholder": "在 theporndb.net 的 API Tokens 页创建，需 read 权限",
                            "type": "password",
                        },
                    },
                    {
                        "component": "VTextarea",
                        "props": {
                            "model": "library_dirs",
                            "label": "媒体库目录（每行一个）",
                            "rows": 4,
                            "placeholder": "/media/XXX",
                        },
                    },
                    {
                        "component": "VSwitch",
                        "props": {
                            "model": "overwrite_nfo",
                            "label": "覆盖已有 movie.nfo",
                        },
                    },
                    {
                        "component": "VSwitch",
                        "props": {
                            "model": "download_poster",
                            "label": "下载海报 poster.jpg",
                        },
                    },
                    {
                        "component": "VSwitch",
                        "props": {
                            "model": "stashdb_enabled",
                            "label": "启用 StashDB 补充源",
                            "hint": "ThePornDB 未命中时回退到 StashDB 搜索。",
                            "persistentHint": True,
                        },
                    },
                    {
                        "component": "VTextField",
                        "props": {
                            "model": "stashdb_api_key",
                            "label": "StashDB API Key",
                            "placeholder": "在 stashdb.org 个人页复制（可选）",
                            "type": "password",
                        },
                    },
                    {
                        "component": "VTextField",
                        "props": {
                            "model": "interval_minutes",
                            "label": "定时刮削间隔（分钟）",
                            "placeholder": "10",
                            "hint": "每轮之间的等待时间，默认 10 分钟。",
                            "persistentHint": True,
                            "class": "mt-6",
                        },
                    },
                    {
                        "component": "VTextField",
                        "props": {
                            "model": "batch_size",
                            "label": "每轮刮削数量",
                            "placeholder": "50",
                            "hint": "每轮最多处理的条目数。",
                            "persistentHint": True,
                            "class": "mt-4",
                        },
                    },
                ],
            }
        ], {
            "enabled": False,
            "api_token": "",
            "library_dirs": "/media/XXX",
            "overwrite_nfo": False,
            "download_poster": True,
            "stashdb_enabled": False,
            "stashdb_api_key": "",
            "interval_minutes": 10,
            "batch_size": 50,
        }

    def get_page(self) -> Optional[List[Dict[str, Any]]]:
        """返回插件详情页面。"""
        if not self._enabled:
            return [
                {
                    "component": "VAlert",
                    "props": {
                        "type": "warning",
                        "variant": "tonal",
                        "text": "插件未启用，请先在配置中启用并填写 API Token。",
                    },
                }
            ]
        return [
            {
                "component": "VAlert",
                "props": {
                    "type": "info",
                    "variant": "tonal",
                    "text": (f"已启用，刮削目录：{', '.join(self._library_dirs) or '未配置'}。"
                            " 可通过 /tpdb_scrape 命令或页面按钮触发全库刮削。"),
                },
            }
        ]

    def stop_service(self) -> None:
        """停止插件后台服务，关闭海报下载线程池。"""
        global _poster_executor
        if _poster_executor is not None:
            _poster_executor.shutdown(wait=False, cancel_futures=False)
            _poster_executor = None
        return None

    def get_service(self) -> List[Dict[str, Any]]:
        """返回插件定时服务，用于增量刮削。

        每 interval_minutes 分钟运行一次，每次处理最多 batch_size 个
        尚未生成 movie.nfo 的条目目录，直到全库消化完，之后自然转为增量。
        """
        if not self._enabled or not self._api_token:
            return []
        return [
            {
                "id": "TpdbScraperIncremental",
                "name": f"{self.plugin_name}增量刮削",
                "trigger": "interval",
                "func": self.incremental_scrape,
                "kwargs": {"minutes": self._interval_minutes},
            }
        ]

    def incremental_scrape(self) -> None:
        """增量刮削：处理一批尚未生成 movie.nfo 的条目目录。

        每次运行处理最多 batch_size 个目录，未命中或已刮削的目录会被
        持久化记录，避免重复处理。
        """
        if not self._enabled or not self._api_token:
            return
        # 读取已处理目录记录（复用进度文件思路，用插件数据保存）
        processed = self.get_data("processed_dirs") or []
        processed_set = set(processed)

        batch_left = max(1, self._batch_size)
        for lib_dir in self._library_dirs:
            root = Path(lib_dir)
            if not root.is_dir():
                continue
            for entry in self._iter_entry_dirs(root):
                if batch_left <= 0:
                    break
                key = str(entry)
                if key in processed_set:
                    continue
                # 已有 movie.nfo 且不覆盖，视为已处理
                if (entry / "movie.nfo").exists() and not self._overwrite_nfo:
                    processed_set.add(key)
                    processed.append(key)
                    continue
                try:
                    self.scrape_one(entry)
                except Exception as exc:  # noqa: BLE001
                    logger.error("ThePornDB 成人刮削：增量刮削失败 %s：%s", entry, exc)
                processed_set.add(key)
                processed.append(key)
                batch_left -= 1
            if batch_left <= 0:
                break

        # 控制持久化规模，仅保留最近处理记录
        self.save_data("processed_dirs", processed[-50000:])
        logger.info("ThePornDB 成人刮削：增量刮削一轮完成，累计处理 %d 个目录",
                    len(processed))

    # ------------------------------------------------------------------ #
    # 事件处理
    # ------------------------------------------------------------------ #

    @eventmanager.register(EventType.PluginAction)
    def on_plugin_action(self, event: Event) -> None:
        """响应 /tpdb_scrape 命令，执行全库刮削。"""
        if not self._enabled:
            return
        event_data = event.event_data or {}
        if event_data.get("action") != "tpdb_scrape":
            return
        user = event_data.get("user")
        channel = event_data.get("channel")
        try:
            result = self.scrape_all()
            self.post_message(
                channel=channel,
                userid=user,
                title="ThePornDB 成人刮削",
                text=(f"全库刮削完成：共 {result.get('total', 0)} 个条目目录，"
                      f"命中 {result.get('matched', 0)}，"
                      f"失败 {result.get('failed', 0)}。"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("ThePornDB 成人刮削：全库刮削异常：%s", exc)
            self.post_message(
                channel=channel,
                userid=user,
                title="ThePornDB 成人刮削",
                text=f"全库刮削失败：{exc}",
            )

    # ------------------------------------------------------------------ #
    # 对外 API
    # ------------------------------------------------------------------ #

    def api_scrape_now(self) -> Dict[str, Any]:
        """处理 /scrape_now 请求，立即执行全库刮削。"""
        if not self._enabled:
            return {"success": False, "message": "插件未启用"}
        if not self._api_token:
            return {"success": False, "message": "未配置 ThePornDB API Token"}
        result = self.scrape_all()
        return {"success": True, "data": result}

    def api_status(self) -> Dict[str, Any]:
        """返回插件当前配置与统计。"""
        return {
            "success": True,
            "data": {
                "enabled": self._enabled,
                "has_token": bool(self._api_token),
                "library_dirs": self._library_dirs,
                "last_result": self.get_data("last_result"),
            },
        }

    # ------------------------------------------------------------------ #
    # 刮削主流程
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> Dict[str, Any]:
        """遍历配置的媒体库目录，对每个条目目录执行刮削。

        :return: 统计结果字典。
        """
        total = 0
        matched = 0
        failed = 0
        for lib_dir in self._library_dirs:
            root = Path(lib_dir)
            if not root.is_dir():
                logger.warning("ThePornDB 成人刮削：库目录不存在，跳过 %s", lib_dir)
                continue
            for entry in self._iter_entry_dirs(root):
                total += 1
                try:
                    if self.scrape_one(entry):
                        matched += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error("ThePornDB 成人刮削：刮削失败 %s：%s", entry, exc)
                    failed += 1
        result = {"total": total, "matched": matched, "failed": failed,
                  "finished_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        self.save_data("last_result", result)
        logger.info("ThePornDB 成人刮削：全库刮削完成，共 %d，命中 %d，失败 %d",
                    total, matched, failed)
        return result

    def scrape_one(self, entry_dir: Path) -> bool:
        """刮削单个条目目录。

        :param entry_dir: 条目目录路径。
        :return: 是否命中并写入元数据。
        """
        if not _is_entry_dir(entry_dir):
            return False
        nfo_path = entry_dir / "movie.nfo"
        if nfo_path.exists() and not self._overwrite_nfo:
            return False

        title = self._clean_title(entry_dir.name)
        kind = self._detect_kind(entry_dir.name)
        if kind == "jav":
            title = self._normalize_jav(title)
        else:
            # scene 与 movie 共用带数字清理的标题提炼。
            title = self._clean_scene_title(entry_dir.name)
        resource = self._search(title, kind)
        if resource is None:
            # 纯演员名目录回退到演员级 NFO。
            if self._is_actor_only(entry_dir.name) and self._try_actor_nfo(entry_dir):
                return True
            logger.debug("ThePornDB 成人刮削：未命中 %s（kind=%s）", entry_dir, kind)
            return False

        if not self._is_reliable_match(entry_dir.name, resource, kind):
            # 命中不可信时，纯演员名目录同样回退到演员级 NFO。
            if self._is_actor_only(entry_dir.name) and self._try_actor_nfo(entry_dir):
                return True
            logger.info("ThePornDB 成人刮削：命中可信度不足，跳过 %s", entry_dir)
            return False

        self._write_nfo(entry_dir, resource)
        if self._download_poster:
            self._download_image(resource, entry_dir)
        return True

    # ------------------------------------------------------------------ #
    # ThePornDB API 调用
    # ------------------------------------------------------------------ #

    def _request(self, endpoint: str, params: Dict[str, Any],
                 retries: int = 3) -> Dict[str, Any]:
        """调用 ThePornDB REST API，带限流退避。

        遇到 429（限流）或 5xx（服务端错误）时按指数退避重试，
        避免连续请求触发更严厉的限流。

        :param endpoint: 端点路径，如 /scenes。
        :param params: 查询参数。
        :param retries: 最大重试次数。
        :return: 解析后的 JSON 响应。
        """
        # 温和限速：保证相邻请求间隔至少 _REQUEST_MIN_INTERVAL 秒。
        global _last_request_ts
        elapsed = time.time() - _last_request_ts
        if elapsed < _REQUEST_MIN_INTERVAL:
            time.sleep(_REQUEST_MIN_INTERVAL - elapsed)
        _last_request_ts = time.time()

        url = f"{_TPDB_API}{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self._api_token}",
            "Accept": "application/json",
            "User-Agent": "MoviePilot-TpdbScraper/1.0",
        })
        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code in (401, 403):
                    # 鉴权失败，重试无意义，直接抛给上层。
                    raise
                if exc.code == 429 or 500 <= exc.code < 600:
                    # 限流或服务端错误：退避后重试。
                    if attempt < retries:
                        delay = 2 ** attempt * 2  # 2、4、8 秒
                        logger.warning(
                            "ThePornDB 成人刮削：HTTP %d 限流/服务端错误，%d 秒后重试（第 %d/%d 次）",
                            exc.code, delay, attempt + 1, retries)
                        time.sleep(delay)
                        continue
                # 其他 HTTP 错误不重试。
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < retries:
                    delay = 2 ** attempt * 2
                    logger.warning(
                        "ThePornDB 成人刮削：请求异常 %s，%d 秒后重试（第 %d/%d 次）",
                        exc, delay, attempt + 1, retries)
                    time.sleep(delay)
                    continue
                raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("ThePornDB 请求失败")

    def _search(self, title: str, kind: str) -> Optional[Dict[str, Any]]:
        """按标题在指定类别下搜索 ThePornDB。

        :param title: 清理后的标题。
        :param kind: 探测类别，scene/jav/movie。
        :return: 命中的资源字典，未命中返回 None。
        """
        for endpoint in self._endpoints_for(kind):
            try:
                data = self._request(endpoint, {
                    "q": title, "per_page": _PER_PAGE,
                })
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    logger.error("ThePornDB 成人刮削：鉴权失败（HTTP %d），请检查 API Token", exc.code)
                    raise
                logger.warning("ThePornDB 成人刮削：请求失败 %s（%s）：%s", endpoint, title, exc)
                continue
            except Exception as exc:  # noqa: BLE001
                logger.warning("ThePornDB 成人刮削：请求异常 %s（%s）：%s", endpoint, title, exc)
                continue
            items = (data or {}).get("data") or []
            if items:
                return items[0]
        # ThePornDB 未命中时，回退到 StashDB 补充源。
        if self._stashdb_enabled and self._stashdb_api_key:
            return self._search_stashdb(title)
        return None

    def _search_stashdb(self, title: str) -> Optional[Dict[str, Any]]:
        """在 StashDB（Stash-box）补充源中按标题搜索场景。

        调用 stashdb.org 的 GraphQL searchScenes 查询，将命中的首个场景
        转换为与 ThePornDB 资源一致的字段结构，供后续写 NFO 复用。

        :param title: 清理后的标题。
        :return: 规范化后的场景资源字典，未命中返回 None。
        """
        query = (
            "query Scenes($term: String!) {"
            "  searchScenes(term: $term) {"
            "    count"
            "    scenes { id title details release_date code"
            "      studio { name }"
            "      performers { performer { name } }"
            "      tags { name }"
            "      images { url }"
            "    }"
            "  }"
            "}"
        )
        payload = json.dumps({"query": query, "variables": {"term": title}}).encode("utf-8")
        req = urllib.request.Request(
            "https://stashdb.org/graphql",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "ApiKey": self._stashdb_api_key,
                "User-Agent": "MoviePilot-TpdbScraper/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("StashDB 成人刮削：搜索失败 %s：%s", title, exc)
            return None
        result = ((data or {}).get("data") or {}).get("searchScenes") or {}
        scenes = result.get("scenes") or []
        if not scenes:
            return None
        scene = scenes[0]
        # 转换为与 ThePornDB 资源一致的字段结构。
        studio = scene.get("studio") or {}
        performers = scene.get("performers") or []
        tags = scene.get("tags") or []
        images = scene.get("images") or []
        poster = images[0].get("url") if images else ""
        return {
            "id": scene.get("id") or "",
            "title": scene.get("title") or "",
            "description": scene.get("details") or "",
            "date": scene.get("release_date") or "",
            "site": {"name": studio.get("name") or ""},
            "performers": [{"name": p.get("performer", {}).get("name") or ""}
                           for p in performers if isinstance(p, dict)],
            "tags": [{"name": t.get("name") or ""} for t in tags if isinstance(t, dict)],
            "poster": poster,
            "slug": scene.get("code") or "",
        }

    @staticmethod
    def _endpoints_for(kind: str) -> List[str]:
        """按探测类别返回应尝试的端点顺序。"""
        if kind == "jav":
            return ["/jav", "/scenes"]
        if kind == "movie":
            return ["/movies", "/scenes"]
        return ["/scenes", "/jav", "/movies"]

    @staticmethod
    def _is_actor_only(dirname: str) -> bool:
        """判断目录名是否为「纯演员名/站名」类（无数字、词数很少）。

        :param dirname: 目录名。
        :return: 是否为纯演员名/短名。
        """
        if re.search(r"\d", dirname):
            return False
        # 过滤论坛套皮、合集包等。
        low = dirname.lower()
        if "@" in dirname or re.search(r"megapack|mega[ _-]?pack|合集", low):
            return False
        words = [w for w in re.split(r"[\s_.-]+", dirname)
                 if w and re.search(r"[A-Za-z]", w)]
        return 1 <= len(words) <= 3

    def _search_performer(self, name: str) -> Optional[Dict[str, Any]]:
        """按演员名搜索 ThePornDB 演员。

        :param name: 演员名。
        :return: 命中的演员资源字典，未命中返回 None。
        """
        try:
            data = self._request("/performers", {"q": name, "per_page": 3})
        except Exception as exc:  # noqa: BLE001
            logger.warning("ThePornDB 成人刮削：演员搜索失败 %s：%s", name, exc)
            return None
        items = (data or {}).get("data") or []
        if not items:
            return None
        # 取 name 与输入最匹配的第一项。
        return items[0]

    def _try_actor_nfo(self, entry_dir: Path) -> bool:
        """对纯演员名目录，回退生成「演员级」NFO。

        :param entry_dir: 条目目录路径。
        :return: 是否成功写入演员级 NFO。
        """
        name = self._clean_title(entry_dir.name).strip(" -_.")
        if not name:
            return False
        performer = self._search_performer(name)
        if performer is None:
            return False
        self._write_actor_nfo(entry_dir, performer)
        if self._download_poster:
            self._download_actor_image(performer, entry_dir)
        return True

    def _write_actor_nfo(self, entry_dir: Path, performer: Dict[str, Any]) -> None:
        """将演员信息写成「演员级」movie.nfo。

        :param entry_dir: 条目目录路径。
        :param performer: ThePornDB 演员资源字典。
        """
        name = performer.get("name") or entry_dir.name
        bio = performer.get("bio") or ""
        birth = performer.get("extras", {}) or {}
        if isinstance(birth, dict):
            birth = ""
        lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            "<movie>",
            f"  <title>{_xml_escape(str(name))}</title>",
            f"  <originaltitle>{_xml_escape(str(name))}</originaltitle>",
        ]
        if bio:
            lines.append(f"  <plot>{_xml_escape(str(bio))}</plot>")
        lines.append(f"  <tagline>{_xml_escape('ThePornDB 演员')}</tagline>")
        if performer.get("id"):
            lines.append(
                f"  <uniqueid type=\"tpdb_performer\" default=\"true\">{_xml_escape(str(performer.get('id')))}</uniqueid>")
        lines.append("</movie>")
        (entry_dir / "movie.nfo").write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("ThePornDB 成人刮削：已写入演员级 movie.nfo：%s", entry_dir / "movie.nfo")

    def _download_actor_image(self, performer: Dict[str, Any], entry_dir: Path) -> None:
        """将演员头像下载任务提交到后台线程池，不阻塞主流程。

        :param performer: ThePornDB 演员资源字典。
        :param entry_dir: 条目目录路径。
        """
        target = entry_dir / "poster.jpg"
        if target.exists():
            return
        image = performer.get("image") or performer.get("thumbnail") or ""
        if not image:
            return
        _get_poster_executor().submit(self._fetch_poster, image, target)

    @staticmethod
    def _is_reliable_match(dirname: str, resource: Dict[str, Any], kind: str) -> bool:
        """判断搜索命中是否可信，避免纯演员名/模糊标题的错配。

        规则：
        - JAV 番号命中天然可信（番号是唯一精确 ID）。
        - 目录名较长（≥3 个核心词，实为「站名/演员 + 完整标题」）时，
          q 全文搜索本身已足够精准，直接放行。
        - 目录名很短（1~2 个词，疑似纯演员名/站名）时严格校验：
          要求目录名核心词与命中 title 高度一致，否则跳过，避免
          一个演员名匹配到该演员的某部非目标片。

        :param dirname: 原始目录名。
        :param resource: ThePornDB 命中资源。
        :param kind: 探测类别。
        :return: 是否可信。
        """
        if kind == "jav":
            return True
        matched_title = (resource.get("title") or "").lower()
        if not matched_title:
            return False

        # 目录名清洗后提取核心词（字母数字，长度 ≥3，去数字单词）。
        cleaned = dirname.lower()
        cleaned = re.sub(r"\.(com|net|org|tv|info)\b", " ", cleaned)
        cleaned = re.sub(r"@[^@\s]+", " ", cleaned)
        words = [w for w in re.split(r"[^a-z0-9]+", cleaned)
                 if len(w) >= 3 and not w.isdigit()]
        if not words:
            return False

        # 长标题（≥3 词）直接放行：目录名本身就是完整标题描述。
        if len(words) >= 3:
            return True

        # 短输入（1~2 词，疑似演员名/站名）：要求命中 title 覆盖全部核心词。
        overlap = sum(1 for w in words if w in matched_title)
        return overlap == len(words)

    # ------------------------------------------------------------------ #
    # NFO 写入与海报下载
    # ------------------------------------------------------------------ #

    def _write_nfo(self, entry_dir: Path, resource: Dict[str, Any]) -> None:
        """将 ThePornDB 资源写成 movie.nfo 落盘。

        :param entry_dir: 条目目录路径。
        :param resource: ThePornDB Scene 资源字典。
        """
        title = resource.get("title") or entry_dir.name
        plot = resource.get("description") or resource.get("synopsis") or ""
        outline = resource.get("outline") or ""
        tagline = resource.get("url") or resource.get("slug") or ""
        year = None
        date = resource.get("date") or ""
        if date:
            year = date[:4]
        uniqueid = resource.get("id") or resource.get("slug") or ""
        studio = ""
        site = resource.get("site") or {}
        if isinstance(site, dict):
            studio = site.get("name") or ""
        performers = resource.get("performers") or []
        tags = resource.get("tags") or []
        directors = resource.get("directors") or []

        lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            "<movie>",
            f"  <title>{_xml_escape(title)}</title>",
            f"  <originaltitle>{_xml_escape(title)}</originaltitle>",
        ]
        if plot:
            lines.append(f"  <plot>{_xml_escape(plot)}</plot>")
        if outline and not plot:
            lines.append(f"  <outline>{_xml_escape(outline)}</outline>")
        if tagline:
            lines.append(f"  <tagline>{_xml_escape(tagline)}</tagline>")
        if year:
            lines.append(f"  <year>{year}</year>")
            lines.append(f"  <premiered>{date}</premiered>")
        if studio:
            lines.append(f"  <studio>{_xml_escape(studio)}</studio>")
        if uniqueid:
            lines.append(
                f"  <uniqueid type=\"theporndb\" default=\"true\">{_xml_escape(str(uniqueid))}</uniqueid>")
        for performer in performers:
            name = performer.get("name") if isinstance(performer, dict) else str(performer)
            if name:
                lines.append(f"  <actor><name>{_xml_escape(str(name))}</name></actor>")
        for director in directors:
            name = director.get("name") if isinstance(director, dict) else str(director)
            if name:
                lines.append(f"  <director>{_xml_escape(str(name))}</director>")
        for tag in tags:
            name = tag.get("name") if isinstance(tag, dict) else str(tag)
            if name:
                lines.append(f"  <tag>{_xml_escape(str(name))}</tag>")
        lines.append("</movie>")

        nfo_path = entry_dir / "movie.nfo"
        nfo_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("ThePornDB 成人刮削：已写入 movie.nfo：%s", nfo_path)

    @staticmethod
    def _fetch_poster(image: str, target: Path) -> None:
        """后台下载单张海报并保存到目标路径（供线程池调用）。

        :param image: 海报图片 URL。
        :param target: 目标文件路径（通常为 poster.jpg）。
        """
        try:
            req = urllib.request.Request(
                image, headers={"User-Agent": "MoviePilot-TpdbScraper/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                target.write_bytes(resp.read())
            logger.info("ThePornDB 成人刮削：已下载海报：%s", target)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ThePornDB 成人刮削：海报下载失败 %s：%s", image, exc)

    def _download_image(self, resource: Dict[str, Any], entry_dir: Path) -> None:
        """将海报下载任务提交到后台线程池，不阻塞主刮削流程。

        :param resource: ThePornDB 资源字典。
        :param entry_dir: 条目目录路径。
        """
        target = entry_dir / "poster.jpg"
        if target.exists():
            return
        image = resource.get("poster") or resource.get("poster_image") \
            or resource.get("image") or ""
        if not image:
            return
        _get_poster_executor().submit(self._fetch_poster, image, target)

    # ------------------------------------------------------------------ #
    # 识别与辅助
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_kind(dirname: str) -> str:
        """根据目录名探测 ThePornDB 类别。

        规则（按优先级）：
        1. 目录名命中 JAV 番号关键词（如 jav/ipx/atid 等），判 jav。
        2. 目录名「整体」是一个 JAV 番号词元（开头就是番号，后跟标题或结尾），
           判 jav；仅当番号是目录名开头时才算，避免把欧美标题里偶然的
           「单词+数字」（如 Lovers 16、Scene1）误判成番号。
        3. 含独立年份，判 movie。
        4. 其余判 scene（欧美场景）。

        :param dirname: 目录名。
        :return: scene/jav/movie。
        """
        lower = dirname.lower()
        # 1. 番号关键词命中。
        if any(h in lower for h in _JAV_HINTS):
            return "jav"
        # 2. 目录名以「番号词元」开头（番号 + 可选标题/年月）。
        m = re.match(
            r"^\s*(?P<code>[A-Z]{2,6})\s*[-_.\s]?\s*(?P<num>\d{2,5})\b",
            dirname, flags=re.IGNORECASE)
        if m:
            return "jav"
        # 3. 含独立年份。
        if re.search(r"\b(19|20)\d{2}\b", dirname):
            return "movie"
        return "scene"

    @staticmethod
    def _clean_title(dirname: str) -> str:
        """清理目录名，去除与数字无关的噪声（分辨率/后缀/论坛套皮等）。

        数字相关的清理（尾缀序号、日期、数字前缀）不在此处处理，
        避免误删 JAV 番号；由 _clean_scene_title 仅对欧美场景使用。

        :param dirname: 原始目录名。
        :return: 清理后的标题。
        """
        title = dirname
        # 去分辨率/编码等噪声。
        title = re.sub(r"[-_. ]+(1080p|720p|480p|2160p|4k|UHD|WEB-DL|WEBRip|BluRay|H\.?26[45]|x26[45]|HEVC|AAC|AC3|DDP?5\.1|XXX|MP4|SD|HD)([-_. ]|$)",
                       " ", title, flags=re.IGNORECASE)
        # 去网站后缀（.com / .net / .org 等）。
        title = re.sub(r"\.(com|net|org|tv|info)\b", " ", title, flags=re.IGNORECASE)
        # 剥离论坛/网盘套皮前缀：形如 发布者@论坛@真正标题。
        # 连续用 @ 分段，取最后一段作为真正标题（前段多为发布者/论坛标识）。
        parts = [p for p in title.split("@") if p.strip()]
        if len(parts) >= 2:
            title = parts[-1].strip()
        # 去掉论坛/网盘中文明示词与网盘标记。
        title = re.sub(
            r"[\s_\-]*(草榴社区|草榴社區|草榴|第一会所|六月天空|sexinsex|t66y|18p2p|baidu|115|夸克|阿里云盘|度盘|單掛|資訊交流網|色中色|sex8|情色|成人论坛)[\s_\-]*",
            " ", title, flags=re.IGNORECASE)
        # 去无意义词（合集包、空目录名、集数标记等，不含数字尾部处理）。
        title = re.sub(r"\b(megapack|mega[ _-]?pack|pack|by \w+|videos)\b",
                       " ", title, flags=re.IGNORECASE)
        # 去清理后残留的空括号。
        title = re.sub(r"\(\s*\)", " ", title)
        title = re.sub(r"\[\s*\]", " ", title)
        title = re.sub(r"\s+", " ", title).strip(" -_.")
        # 若残留仍含中文，提取其中的英文/数字片段作为搜索标题
        # （ThePornDB 只收录西文标题，中文描述无法命中）。
        if re.search(r"[\u4e00-\u9fff]", title):
            eng_parts = re.findall(r"[A-Za-z0-9][A-Za-z0-9'.& \-]*[A-Za-z0-9]", title)
            if eng_parts:
                title = " ".join(p.strip(" -_.") for p in eng_parts if p.strip(" -_."))
        return title or dirname

    @staticmethod
    def _clean_scene_title(dirname: str) -> str:
        """清理欧美场景目录名（含数字噪声处理）。

        在基础清理之上，额外去除：年份、年份范围、集数标记、数字前缀、
        尾缀序号、短日期片段，把目录名提炼成「站名/演员 + 标题关键词」。

        :param dirname: 原始目录名。
        :return: 清理后的标题。
        """
        title = dirname
        # 基础清理（复用通用逻辑）。
        title = TpdbScraper._clean_title(title)
        # 去年份与年份范围。
        title = re.sub(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b", " ", title)
        title = re.sub(r"\b(19|20)\d{2}\b", " ", title)
        # 去集数/序号标记。
        title = re.sub(r"\b(part\s*\d+|scene\s*\d+|disc\s*\d+|cd\s*\d+|sc\s*\d+|s\d{1,2}e\d{1,2})\b",
                       " ", title, flags=re.IGNORECASE)
        title = re.sub(r"#\s*\d+", " ", title)
        # 去开头的纯数字前缀。
        title = re.sub(r"^\d+\s+", " ", title)
        # 去结尾的「空格+数字」序号（如 Lovers 16、Trans-Active 17、- 1）。
        title = re.sub(r"\s+[-–]?\s*\d{1,3}\s*$", " ", title)
        # 去「YY MM DD」/「M D YY」短日期片段。
        title = re.sub(r"\b\d{2}\s+\d{2}\s+\d{2}\b", " ", title)
        title = re.sub(r"\b\d{1,2}\s+\d{1,2}\s+\d{2}\b", " ", title)
        title = re.sub(r"\(\s*\)", " ", title)
        title = re.sub(r"\[\s*\]", " ", title)
        title = re.sub(r"\s+", " ", title).strip(" -_.")
        return title or dirname

    @staticmethod
    def _normalize_jav(title: str) -> str:
        """规范 JAV 番号：字母与数字之间的空格/下划线/点/连字符统一为连字符。

        仅对已判定为 jav 的目录标题使用，避免误伤欧美场景标题。

        :param title: 清理后的标题。
        :return: 番号规范化后的标题。
        """
        return re.sub(
            r"(?<![A-Z0-9])([A-Z]{2,6})\s*[-_.]?\s*(\d{2,5})(?![A-Z0-9])",
            r"\1-\2", title or "", flags=re.IGNORECASE)

    @staticmethod
    def _iter_entry_dirs(root: Path):
        """遍历库根目录下的条目目录。

        条目目录定义为「直接含视频文件的目录」，跳过分类父目录本身与
        trickplay 等元数据子目录。

        :param root: 库根目录。
        :return: 条目目录生成器。
        """
        for entry in sorted(root.rglob("*")):
            if not entry.is_dir():
                continue
            if "trickplay" in entry.name.lower():
                continue
            if _is_entry_dir(entry):
                yield entry


def _is_entry_dir(path: Path) -> bool:
    """判断目录是否为可直接刮削的条目目录。"""
    try:
        return any(_is_video(child) for child in path.iterdir())
    except OSError:
        return False


__all__ = ["TpdbScraper"]
