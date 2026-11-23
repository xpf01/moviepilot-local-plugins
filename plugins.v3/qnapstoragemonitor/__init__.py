"""QNAP 存储池容量监控插件。

通过 SSH 登录 QNAP 宿主机，读取存储池（CACHEDEV 数据卷）的容量使用情况。
当剩余容量低于「停止下载阈值」时暂停下载器所有正在下载的任务（保留做种/上传），
并通过 MoviePilot 通知渠道推送告警；当容量回升到「恢复下载阈值」之上时自动恢复下载。
两个阈值可独立配置，也可手动恢复。使用系统命令 sshpass + ssh 连接 QNAP，
复用 MoviePilot 内置 Transmission 客户端控制下载任务，不依赖额外的 Python 依赖。

空间不足时，除删除刚添加的下载任务外，还会把触发该下载的订阅置为暂停（state=S），
避免订阅在下一轮搜索中再次命中同一资源、形成「添加→删除→再添加」的死循环；
容量回升到恢复阈值后，被本插件暂停的订阅会随之自动恢复。
"""

import json
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.triggers.cron import CronTrigger

from app.application.downloader import DownloaderHelper
from app.db.oper.subscribe import SubscribeOper
from app.modules.transmission.transmission import Transmission
from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.schemas.types import EventType
from app.sdk.events import eventmanager
from app.sdk.logging import logger


class QnapStorageMonitor(_PluginBase):
    """QNAP 存储池容量监控插件。"""

    plugin_name = "QNAP存储池监控"
    plugin_desc = "定时监控 QNAP 存储池容量，低于阈值暂停下载、高于阈值自动恢复，并推送告警。"
    plugin_icon = "qnapstoragemonitor.png"
    plugin_version = "1.0.2"
    plugin_label = "系统工具,监控,存储"
    plugin_author = "local"
    plugin_config_prefix = "qnapstoragemonitor_"
    plugin_order = 30
    auth_level = 1

    # 默认只监控 CACHEDEV 数据卷，忽略系统缓存/引导卷
    _MONITOR_PREFIX = "CACHEDEV"

    _enabled = False
    _host = ""
    _port = 22
    _username = ""
    _password = ""
    _interval_hours = 12
    _cron = "0 * * * *"
    _stop_threshold_gb = 500.0
    _resume_threshold_gb = 2000.0
    _auto_pause_download = True
    _monitor_all = False
    _monitor_pool = ""
    _onlyonce = False
    # 手动任务豁免：开启时，仅拦截订阅自动触发（source 以 Subscribe 开头）的下载，
    # 手动添加（source=Manual 或其它非订阅来源）的任务不删除，避免误伤用户手动下载。
    _exempt_manual = True
    # 拦截后连带暂停订阅：开启时，删除下载任务后把对应订阅置为暂停（state=S），
    # 避免订阅在下一轮搜索中再次命中同一资源，形成「添加→删除→再添加」的死循环。
    _pause_subscribe_on_block = True

    # 下载暂停状态标记，保存到插件数据，重启后可续
    _download_paused = False
    # 会触发自动搜索的订阅状态：R（订阅中）与 P（待定，允许搜索但不允许完成）。
    # 只有这两个状态需要暂停才能阻断反复重下；N 未处理、S 已暂停无需干预。
    _SEARCHABLE_STATES = ("R", "P")
    # 被本插件暂停的订阅：{订阅ID(str): {name, media_id, season, original_state, paused_at, hash}}
    # 只记录本插件暂停的订阅，容量恢复后据此精确回滚，不碰用户自己暂停的订阅。
    _paused_subscribes: Dict[str, Dict[str, Any]] = {}

    # 磁盘容量查询缓存（避免 DownloadAdded 事件高频触发时反复 SSH）：(查询时间戳, 最小剩余GB, 剩余最少池名)
    _disk_cache: Optional[Tuple[float, float, str]] = None
    # 磁盘查询缓存有效期（秒）：窗口内的重复查询直接复用缓存结果
    _DISK_CACHE_TTL = 60.0
    # 事件处理器加锁，避免并发下载事件同时操作下载器/磁盘状态
    _react_lock = threading.Lock()

    def init_plugin(self, config: dict = None) -> None:
        """根据插件配置初始化运行状态。

        :param config: 插件配置字典。
        """
        self.stop_service()
        self._enabled = False
        if not config:
            return
        self._enabled = bool(config.get("enabled"))
        self._host = str(config.get("host") or "").strip()
        self._port = int(config.get("port") or 22)
        self._username = str(config.get("username") or "").strip()
        self._password = str(config.get("password") or "")
        self._interval_hours = int(config.get("interval_hours") or 12)
        self._cron = str(config.get("cron") or "0 * * * *")
        self._stop_threshold_gb = float(config.get("stop_threshold_gb") or 500)
        self._resume_threshold_gb = float(config.get("resume_threshold_gb") or 2000)
        self._auto_pause_download = bool(config.get("auto_pause_download"))
        self._monitor_all = bool(config.get("monitor_all"))
        self._monitor_pool = str(config.get("monitor_pool") or "").strip()
        self._onlyonce = bool(config.get("onlyonce"))
        # exempt_manual 缺省视为 True（默认豁免手动任务，避免误删）
        self._exempt_manual = bool(config.get("exempt_manual", True))
        # pause_subscribe_on_block 缺省视为 True（默认连带暂停订阅，防反复添加）
        self._pause_subscribe_on_block = bool(config.get("pause_subscribe_on_block", True))
        # 恢复上次的下载暂停状态，保证重启后状态一致
        self._download_paused = bool(self.get_data("download_paused"))
        # 恢复被本插件暂停的订阅清单（dict，键为字符串化的订阅 ID）
        saved_paused = self.get_data("paused_subscribes")
        self._paused_subscribes = dict(saved_paused) if isinstance(saved_paused, dict) else {}
        if self._enabled and self._onlyonce:
            threading.Thread(target=self._check_and_react, daemon=True).start()

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def get_service(self) -> List[Dict[str, Any]]:
        """注册插件定时服务，按配置周期轮询存储池容量。"""
        if not self._enabled or not self._host or not self._username:
            return []
        return [{
            "id": "QnapStorageMonitor",
            "name": "QNAP存储池容量监控",
            "trigger": CronTrigger.from_crontab(self._cron),
            "func": self._check_and_react,
            "kwargs": {}
        }]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表，提供状态查看与立即检查端点。"""
        return [
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "查看最近检查结果与暂停状态",
            },
            {
                "path": "/check_now",
                "endpoint": self.api_check_now,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即执行一次容量检查",
            },
        ]

    def api_status(self) -> Dict[str, Any]:
        """返回插件运行状态摘要，供 Vue 详情页展示。

        :return: 包含启用状态、最近检查报告与下载暂停状态的字典。
        """
        return {
            "success": True,
            "data": {
                "enabled": self._enabled,
                "download_paused": self._download_paused,
                "paused_subscribe_count": len(self._paused_subscribes),
                "last_report": self.get_data("last_report") or "",
            },
        }

    def api_check_now(self) -> Dict[str, Any]:
        """立即执行一次容量检查，供 Vue 详情页触发。"""
        if not self._enabled:
            return {"success": False, "message": "插件未启用"}
        self._check_and_react()
        return {
            "success": True,
            "message": "检查完成",
            "data": {
                "download_paused": self._download_paused,
                "paused_subscribe_count": len(self._paused_subscribes),
                "last_report": self.get_data("last_report") or "",
            },
        }

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回插件默认配置（Vue 模式下表单由远程 Config 组件渲染）。"""
        return [], {
            "enabled": False,
            "host": "192.168.1.11",
            "port": 22,
            "username": "",
            "password": "",
            "cron": "0 * * * *",
            "stop_threshold_gb": 500,
            "resume_threshold_gb": 2000,
            "auto_pause_download": True,
            "monitor_all": False,
            "monitor_pool": "",
            "onlyonce": False,
            "exempt_manual": True,
            "pause_subscribe_on_block": True,
        }

    def get_page(self) -> Optional[List[dict]]:
        """返回插件详情页面（Vue 模式下由远程 Page 组件渲染）。"""
        return []

    def stop_service(self) -> None:
        """停止插件后台服务并释放资源。"""
        return None

    @eventmanager.register(EventType.DownloadAdded)
    def remote_download_added(self, event):
        """下载添加事件处理器：下载一旦被添加，立即检查磁盘并在不足时删除该任务。

        这是对「定时巡检」的即时补充：定时巡检最长 12 小时才响应一次，而下载添加事件
        能在下载刚建立（进度约 0%、尚未占用新空间）时就触发检查，把磁盘风险窗口压缩到秒级。
        磁盘查询结果带 60 秒缓存，避免批量下载并发触发时反复 SSH 查询 QNAP。
        开启「手动任务豁免」时，仅拦截订阅自动触发（source 以 Subscribe 开头）的任务，
        手动添加（source=Manual 或其它非订阅来源）不删除，避免误伤用户手动下载。

        开启「拦截后暂停订阅」时，删除下载任务后还会把触发该下载的订阅置为暂停（state=S），
        否则订阅下一轮搜索仍会命中同一批资源，形成「添加→删除→再添加」的无限循环。
        """
        if not self._enabled or not self._auto_pause_download:
            return
        if getattr(event, "event_data", None):
            data = event.event_data
        else:
            data = event
        download_hash = getattr(data, "hash", None) or (data.get("hash") if isinstance(data, dict) else None)
        if not download_hash:
            return
        source = getattr(data, "source", None) or (data.get("source") if isinstance(data, dict) else None)
        # 手动任务豁免：开启时，非订阅来源（Manual 及其它）直接跳过，不删除。
        if self._exempt_manual:
            if source and not str(source).startswith("Subscribe"):
                return
        # 低频磁盘判断：带缓存，避免每个下载都 SSH 一次
        min_info = self._query_min_avail_cached()
        if min_info is None:
            return
        pool_name, avail_gb = min_info
        if avail_gb >= self._stop_threshold_gb:
            return
        # 低于阈值：立即删除这个刚添加的下载任务，不留暂停残留
        with self._react_lock:
            deleted = self._delete_single(download_hash, pool_name, avail_gb)
            if deleted and self._pause_subscribe_on_block:
                self._pause_subscribe_from_source(source, download_hash, pool_name, avail_gb)

    def _parse_subscribe_source(self, source: Any) -> Optional[Dict[str, Any]]:
        """解析订阅来源字符串，取出订阅身份信息。

        MoviePilot 订阅下载的 source 形如 ``Subscribe|{"id": 110, "name": "...", ...}``。

        :param source: 事件 payload 中的 source 字段。
        :return: 解析出的订阅信息字典；非订阅来源或解析失败返回 None。
        """
        if not source:
            return None
        text = str(source).strip()
        if not text.startswith("Subscribe|"):
            return None
        try:
            parsed = json.loads(text.split("|", 1)[1])
        except (IndexError, json.JSONDecodeError, TypeError) as err:
            logger.warning("QNAP存储池监控：解析订阅来源失败 %s", err)
            return None
        return parsed if isinstance(parsed, dict) else None

    def _pause_subscribe_from_source(
        self, source: Any, download_hash: str, pool_name: str, avail_gb: float
    ) -> None:
        """按下载来源暂停对应订阅，防止下一轮搜索重复添加同一资源。

        MoviePilot 订阅状态中，「R（订阅中）」和「P（待定）」都允许自动搜索，
        因此两者都必须暂停，否则订阅仍会在下一轮搜索中重新命中同一资源。
        已被暂停（S）、已完成或已删除的订阅不再处理。
        暂停记录（含原始状态）写入插件数据，容量恢复后据此精确回滚。

        :param source: 事件 payload 中的 source 字段。
        :param download_hash: 被删除的下载任务 hash，用于记录与排查。
        :param pool_name: 剩余容量最少的存储池名。
        :param avail_gb: 该池剩余容量（GB）。
        """
        info = self._parse_subscribe_source(source)
        if not info:
            return
        subscribe_id = info.get("id")
        if subscribe_id is None:
            return
        key = str(subscribe_id)
        try:
            oper = SubscribeOper()
            subscribe = oper.get(int(subscribe_id))
        except Exception as exc:
            logger.error("QNAP存储池监控：读取订阅 %s 失败 %s", subscribe_id, exc)
            return
        if not subscribe:
            logger.warning("QNAP存储池监控：订阅 %s 不存在，跳过暂停", subscribe_id)
            return
        current_state = getattr(subscribe, "state", None)
        if current_state == "S":
            # 已是暂停态：可能上次就是本插件停的，补记一次以便恢复时回滚
            if key not in self._paused_subscribes:
                self._remember_paused_subscribe(key, subscribe, download_hash)
            return
        if current_state not in self._SEARCHABLE_STATES:
            logger.info(
                "QNAP存储池监控：订阅 %s 状态为 %s，不会自动搜索，无需暂停",
                subscribe_id, current_state)
            return
        try:
            # SubscribeOper 未绑定会话时由组合根自行开事务并提交，无需额外 commit
            oper.update(int(subscribe_id), {"state": "S"})
        except Exception as exc:
            logger.error("QNAP存储池监控：暂停订阅 %s 失败 %s", subscribe_id, exc)
            self._notify(
                "QNAP 存储池告警：暂停订阅失败",
                f"存储池 {pool_name} 剩余 {avail_gb:.0f}G 低于阈值，"
                f"已删除下载任务，但暂停订阅「{info.get('name') or subscribe_id}」失败，"
                f"该订阅可能反复重新下载，请手动暂停。")
            return
        self._remember_paused_subscribe(key, subscribe, download_hash)
        logger.info(
            "QNAP存储池监控：已暂停订阅 %s「%s」（原状态 %s），避免重复添加下载",
            subscribe_id, info.get("name") or getattr(subscribe, "name", ""), current_state)
        self._notify(
            "QNAP 存储池告警：已拦截并暂停订阅",
            f"存储池 {pool_name} 剩余仅 {avail_gb:.0f}G，低于停止阈值 "
            f"{self._stop_threshold_gb:.0f}G。\n"
            f"已删除刚添加的下载任务，并暂停订阅「{info.get('name') or subscribe_id}」"
            f"（原状态 {current_state}），避免反复重新下载。容量恢复后将自动恢复该订阅。")

    def _remember_paused_subscribe(self, key: str, subscribe: Any, download_hash: str) -> None:
        """记录被本插件暂停的订阅，供容量恢复后回滚。

        同时记录暂停前的原始状态（R 或 P），恢复时按原状态还原，
        避免把「待定(P)」的订阅错误恢复成「订阅中(R)」。

        :param key: 字符串化的订阅 ID。
        :param subscribe: 订阅记录对象。
        :param download_hash: 触发暂停的下载任务 hash。
        """
        original_state = getattr(subscribe, "state", None)
        # 已处于 S 的订阅可能重复进入本方法，此时保留首次记录的原始状态
        previous = self._paused_subscribes.get(key) or {}
        self._paused_subscribes[key] = {
            "name": getattr(subscribe, "name", "") or "",
            "media_id": str(getattr(subscribe, "tmdbid", "") or ""),
            "season": getattr(subscribe, "season", None),
            "original_state": previous.get("original_state")
            or (original_state if original_state in self._SEARCHABLE_STATES else "R"),
            "paused_at": int(time.time()),
            "hash": download_hash,
        }
        self.save_data("paused_subscribes", self._paused_subscribes)

    def _resume_paused_subscribes(self) -> int:
        """恢复被本插件暂停的订阅，仅回滚自己暂停的那些。

        :return: 成功恢复的订阅数量。
        """
        if not self._paused_subscribes:
            return 0
        recovered = 0
        remaining: Dict[str, Dict[str, Any]] = {}
        try:
            oper = SubscribeOper()
        except Exception as exc:
            logger.error("QNAP存储池监控：初始化订阅操作失败 %s", exc)
            return 0
        for key, info in list(self._paused_subscribes.items()):
            try:
                subscribe = oper.get(int(key))
            except Exception as exc:
                logger.error("QNAP存储池监控：读取订阅 %s 失败 %s", key, exc)
                remaining[key] = info
                continue
            if not subscribe:
                # 订阅已被删除，无需恢复
                logger.info("QNAP存储池监控：订阅 %s 已不存在，移出待恢复清单", key)
                continue
            if getattr(subscribe, "state", None) != "S":
                # 状态已被用户改动，尊重用户选择，不强行覆盖
                logger.info(
                    "QNAP存储池监控：订阅 %s 状态已是 %s，跳过恢复",
                    key, getattr(subscribe, "state", None))
                continue
            try:
                # 还原到暂停前的原始状态（R 或 P），不要一律恢复成 R
                restore_state = str(info.get("original_state") or "R")
                if restore_state not in self._SEARCHABLE_STATES:
                    restore_state = "R"
                # SubscribeOper 未绑定会话时由组合根自行开事务并提交，无需额外 commit
                oper.update(int(key), {"state": restore_state})
            except Exception as exc:
                logger.error("QNAP存储池监控：恢复订阅 %s 失败 %s", key, exc)
                remaining[key] = info
                continue
            recovered += 1
            logger.info(
                "QNAP存储池监控：已恢复订阅 %s「%s」到原状态 %s",
                key, info.get("name") or "", restore_state)
        self._paused_subscribes = remaining
        self.save_data("paused_subscribes", self._paused_subscribes)
        return recovered


    def _query_min_avail_cached(self) -> Optional[Tuple[str, float]]:
        """查询剩余容量最小的存储池，结果带缓存（窗口内复用，避免频繁 SSH）。

        :return: (池名, 剩余GB)；查询失败返回 None。
        """
        import time
        now = time.time()
        if self._disk_cache and (now - self._disk_cache[0]) < self._DISK_CACHE_TTL:
            return self._disk_cache[1], self._disk_cache[2]
        pools = self._query_storage_pools()
        if not pools:
            return None
        min_pool = min(pools, key=lambda x: x[3])
        name, _total, _used, avail = min_pool
        self._disk_cache = (now, float(avail), str(name))
        return str(name), float(avail)

    def _delete_single(self, download_hash: str, pool_name: str, avail_gb: float) -> bool:
        """删除单个刚添加的下载任务，空间不足时不留暂停残留。

        刚添加的任务进度约 0%、尚未落盘任何数据，删除时无需删除文件
        （delete_file=False），只移除下载器中的任务条目。

        :param download_hash: 下载任务 hash。
        :param pool_name: 剩余容量最少的存储池名。
        :param avail_gb: 该池剩余容量（GB）。
        :return: 删除成功返回 True，失败返回 False。
        """
        client = self._get_transmission()
        if not client:
            logger.warning("QNAP存储池监控：下载添加事件触发删除，但无法连接 Transmission")
            return False
        ok = client.delete_torrents(delete_file=False, ids=[download_hash])
        if ok:
            logger.info(
                "QNAP存储池监控：下载添加事件触发，存储池 %s 剩余 %.0fG 低于阈值 %.0fG，已删除新下载任务 %s",
                pool_name, avail_gb, self._stop_threshold_gb, download_hash)
            return True
        logger.warning("QNAP存储池监控：删除新下载任务失败 %s", download_hash)
        return False

    def _check_and_react(self) -> None:
        """执行一次容量检查，并按阈值决定暂停或恢复下载。"""
        if not self._host or not self._username:
            logger.warning("QNAP存储池监控：未配置 SSH 地址或用户名，跳过检查")
            return
        pools = self._query_storage_pools()
        if pools is None:
            self._notify("QNAP 存储池监控", "SSH 连接 QNAP 失败，请检查地址/账号/密码")
            return
        if not pools:
            return

        # 取剩余容量最小的存储池作为判定依据（最紧迫的那个）
        min_pool = min(pools, key=lambda x: x[3])
        min_name, total_gb, used_gb, avail_gb = min_pool

        lines = []
        for name, t, u, a in pools:
            pct = (u / t * 100) if t else 0
            lines.append(f"{name}: 总 {t:.0f}G / 已用 {u:.0f}G / 剩余 {a:.0f}G ({pct:.1f}%)")
        report = "；".join(lines)
        self.save_data("last_report", report)
        logger.info("QNAP存储池监控检查完成：%s", report)

        # 判定：用剩余最少的池对比阈值
        if avail_gb < self._stop_threshold_gb:
            # 低于停止阈值：暂停下载（若尚未暂停）
            if self._auto_pause_download and not self._download_paused:
                if self._pause_downloads():
                    self._download_paused = True
                    self.save_data("download_paused", True)
                    text = (
                        f"存储池 {min_name} 剩余仅 {avail_gb:.0f}G，低于停止阈值 "
                        f"{self._stop_threshold_gb:.0f}G，已自动暂停全部下载任务。\n\n"
                        + "\n".join(lines)
                    )
                    self._notify("QNAP 存储池告警：已暂停下载", text)
                else:
                    self._notify(
                        "QNAP 存储池告警：暂停下载失败",
                        f"存储池 {min_name} 剩余 {avail_gb:.0f}G 已低于阈值，"
                        f"但暂停下载任务失败，请手动处理。\n\n" + "\n".join(lines)
                    )
            else:
                self._notify(
                    "QNAP 存储池容量告警",
                    f"存储池 {min_name} 剩余仅 {avail_gb:.0f}G，低于停止阈值 "
                    f"{self._stop_threshold_gb:.0f}G。\n\n" + "\n".join(lines)
                )
        elif avail_gb > self._resume_threshold_gb:
            # 高于恢复阈值：恢复下载器任务与因空间不足被暂停的订阅。
            # 两者独立判断：可能只发生「拦截单次下载并暂停订阅」而下载器从未整体暂停。
            resumed_notes: List[str] = []
            if self._download_paused:
                if self._resume_downloads():
                    self._download_paused = False
                    self.save_data("download_paused", False)
                    resumed_notes.append("已自动恢复下载器任务")
                else:
                    self._notify(
                        "QNAP 存储池恢复：恢复下载失败",
                        f"存储池 {min_name} 剩余 {avail_gb:.0f}G 已高于恢复阈值，"
                        f"但恢复下载任务失败，请手动处理。"
                    )
            if self._paused_subscribes:
                count = self._resume_paused_subscribes()
                if count:
                    resumed_notes.append(f"已恢复 {count} 个此前因空间不足被暂停的订阅")
            if resumed_notes:
                text = (
                    f"存储池 {min_name} 剩余 {avail_gb:.0f}G，已高于恢复阈值 "
                    f"{self._resume_threshold_gb:.0f}G，" + "，".join(resumed_notes) + "。\n\n"
                    + "\n".join(lines)
                )
                self._notify("QNAP 存储池恢复", text)
        # 介于两阈值之间：维持现状，不动作

    def _get_transmission(self) -> Optional[Transmission]:
        """从 MoviePilot 已配置的下载器里找到 Transmission 并建立连接。

        :return: 连接成功的 Transmission 客户端；未配置或连接失败返回 None。
        """
        try:
            configs = DownloaderHelper().get_configs()
        except Exception as exc:  # pragma: no cover
            logger.error("QNAP存储池监控：读取下载器配置失败 %s", exc)
            return None
        for name, conf in configs.items():
            if conf.type != "transmission":
                continue
            cfg = conf.config or {}
            host = cfg.get("host")
            port = cfg.get("port")
            username = cfg.get("username")
            password = cfg.get("password")
            if not host:
                logger.warning("QNAP存储池监控：Transmission 配置缺少 host")
                continue
            # MoviePilot 部分版本的下载器配置把 host 存成完整 URL（如 http://ip:port），
            # 此时没有独立的 port 字段；内置 Transmission 客户端只传入 host 即可自行解析。
            if port:
                client = Transmission(
                    host=str(host),
                    port=int(port),
                    username=username or None,
                    password=password or None,
                )
            else:
                client = Transmission(
                    host=str(host),
                    username=username or None,
                    password=password or None,
                )
            if client.trc:
                return client
        logger.warning("QNAP存储池监控：未找到可用的 Transmission 下载器")
        return None

    def _pause_downloads(self) -> bool:
        """暂停下载器所有正在下载中的任务，保留做种任务。

        :return: 操作成功返回 True，失败或无任务返回 False。
        """
        client = self._get_transmission()
        if not client:
            return False
        torrents = client.get_downloading_torrents()
        if torrents is None:
            return False
        if not torrents:
            return True  # 没有下载中的任务，视为成功
        ids = [t.hashString for t in torrents if getattr(t, "hashString", None)]
        if not ids:
            return True
        ok = client.stop_torrents(ids=ids)
        if ok:
            logger.info("QNAP存储池监控：已暂停 %d 个下载任务", len(ids))
        return ok

    def _resume_downloads(self) -> bool:
        """恢复下载器所有处于暂停状态的下载任务。

        :return: 操作成功返回 True，失败返回 False。
        """
        client = self._get_transmission()
        if not client:
            return False
        # 恢复：暂停时是通过 stop 停的，这里用 start 恢复全部 stopped 状态任务
        torrents, error = client.get_torrents(status=["stopped"])
        if error or torrents is None:
            return False
        if not torrents:
            return True
        ids = [t.hashString for t in torrents if getattr(t, "hashString", None)]
        if not ids:
            return True
        ok = client.start_torrents(ids=ids)
        if ok:
            logger.info("QNAP存储池监控：已恢复 %d 个下载任务", len(ids))
        return ok

    def _query_storage_pools(self) -> Optional[List[Tuple[str, float, float, float]]]:
        """通过 SSH 读取 QNAP 的 df 输出，解析存储池容量。

        :return: [(名称, 总量GB, 已用GB, 剩余GB), ...]，连接失败返回 None。
        """
        if not self._password:
            logger.warning("QNAP存储池监控：未配置 SSH 密码")
            return None
        cmd = (
            f"sshpass -p {_shell_quote(self._password)} "
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 "
            f"-p {self._port} {self._username}@{self._host} 'df -hP 2>/dev/null'"
        )
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=40
            )
        except subprocess.TimeoutExpired:
            logger.error("QNAP存储池监控：SSH 执行超时")
            return None
        except Exception as exc:  # pragma: no cover
            logger.error("QNAP存储池监控：SSH 执行异常 %s", exc)
            return None

        pools: List[Tuple[str, float, float, float]] = []
        for line in proc.stdout.splitlines():
            if "/share/" not in line:
                continue
            fields = line.split()
            if len(fields) < 6:
                continue
            dev = fields[0]
            mnt = fields[-1]
            size_s, used_s, avail_s = fields[1], fields[2], fields[3]
            name = self._resolve_pool_name(dev, mnt)
            if name is None:
                continue
            total_gb = _parse_size_gb(size_s)
            used_gb = _parse_size_gb(used_s)
            avail_gb = _parse_size_gb(avail_s)
            if total_gb is None or avail_gb is None:
                continue
            pools.append((name, total_gb, used_gb, avail_gb))
        # 去重：同一设备多次挂载只保留一次
        seen = set()
        dedup: List[Tuple[str, float, float, float]] = []
        for item in pools:
            if item[0] in seen:
                continue
            seen.add(item[0])
            dedup.append(item)
        # 解析不出任何存储池数据才判为连接失败（QNAP 的 df 会因无权限 socket 返回码非 0，但 stdout 数据正常）
        if not dedup and not proc.stdout.strip():
            logger.error("QNAP存储池监控：SSH 无有效输出（返回码 %s，stderr %s）",
                         proc.returncode, proc.stderr)
            return None
        return dedup

    def _resolve_pool_name(self, dev: str, mount: str) -> Optional[str]:
        """根据设备名与挂载点解析出存储池显示名。

        :param dev: df 首列设备名（如 /dev/mapper/cachedev2）。
        :param mount: 挂载点（如 /share/CACHEDEV2_DATA）。
        :return: 存储池名；不需要监控时返回 None。
        """
        base = Path(mount).name
        if self._monitor_pool:
            return base if base == self._monitor_pool else None
        if base.startswith(self._MONITOR_PREFIX) and base.endswith("_DATA"):
            return base
        if self._monitor_all and ("CACHEDEV" in base or "cachedev" in dev):
            return base
        return None

    def _notify(self, title: str, text: str) -> None:
        """通过 MoviePilot 通知渠道推送消息。

        :param title: 通知标题。
        :param text: 通知正文。
        """
        try:
            self.post_message(mtype=NotificationType.Plugin, title=title, text=text)
        except Exception as exc:  # pragma: no cover
            logger.error("QNAP存储池监控：发送通知失败 %s", exc)


def _shell_quote(value: str) -> str:
    """用单引号包裹字符串，防止 shell 注入。

    :param value: 需要引用的字符串。
    :return: 单引号包裹后的安全字符串。
    """
    return "'" + str(value).replace("'", "'\\''") + "'"


def _parse_size_gb(value: str) -> Optional[float]:
    """把 df -h 的大小字符串解析为 GB 数值。

    支持 K/M/G/T 后缀与带小数。无法解析返回 None。

    :param value: df -h 输出的大小字段，如 "34.2T"、"620.0G"。
    :return: 换算后的 GB 浮点数。
    """
    if not value:
        return None
    m = re.match(r"^\s*([0-9.]+)\s*([KMGTP]?)\s*$", value, re.IGNORECASE)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2).upper() or "G"
    factor = {"K": 1 / 1024 / 1024, "M": 1 / 1024, "G": 1.0, "T": 1024.0, "P": 1024 * 1024}
    return num * factor.get(unit, 1.0)
