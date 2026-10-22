"""QNAP 存储池容量监控插件。

通过 SSH 登录 QNAP 宿主机，读取存储池（CACHEDEV 数据卷）的容量使用情况。
当剩余容量低于「停止下载阈值」时暂停下载器所有正在下载的任务（保留做种/上传），
并通过 MoviePilot 通知渠道推送告警；当容量回升到「恢复下载阈值」之上时自动恢复下载。
两个阈值可独立配置，也可手动恢复。使用系统命令 sshpass + ssh 连接 QNAP，
复用 MoviePilot 内置 Transmission 客户端控制下载任务，不依赖额外的 Python 依赖。
"""

import re
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.triggers.interval import IntervalTrigger

from app.application.downloader import DownloaderHelper
from app.modules.transmission.transmission import Transmission
from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.sdk.logging import logger


class QnapStorageMonitor(_PluginBase):
    """QNAP 存储池容量监控插件。"""

    plugin_name = "QNAP存储池监控"
    plugin_desc = "定时监控 QNAP 存储池容量，低于阈值暂停下载、高于阈值自动恢复，并推送告警。"
    plugin_icon = "qnapstoragemonitor.png"
    plugin_version = "1.0.0"
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
    _stop_threshold_gb = 500.0
    _resume_threshold_gb = 2000.0
    _auto_pause_download = True
    _monitor_all = False
    _onlyonce = False

    # 下载暂停状态标记，保存到插件数据，重启后可续
    _download_paused = False

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
        self._stop_threshold_gb = float(config.get("stop_threshold_gb") or 500)
        self._resume_threshold_gb = float(config.get("resume_threshold_gb") or 2000)
        self._auto_pause_download = bool(config.get("auto_pause_download"))
        self._monitor_all = bool(config.get("monitor_all"))
        self._onlyonce = bool(config.get("onlyonce"))
        # 恢复上次的下载暂停状态，保证重启后状态一致
        self._download_paused = bool(self.get_data("download_paused"))
        if self._enabled and self._onlyonce:
            threading.Thread(target=self._check_and_react, daemon=True).start()

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        """注册插件定时服务，按配置周期轮询存储池容量。"""
        if not self._enabled or not self._host or not self._username:
            return []
        return [{
            "id": "QnapStorageMonitor",
            "name": "QNAP存储池容量监控",
            "trigger": IntervalTrigger(hours=self._interval_hours),
            "func": self._check_and_react,
            "kwargs": {}
        }]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表，本插件无自定义 API。"""
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """拼装插件配置页面与默认配置。"""
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {"model": "enabled", "label": "启用插件"}
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {"model": "onlyonce", "label": "立即运行一次"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "host", "label": "QNAP 地址", "placeholder": "192.168.1.11"}
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "port", "label": "SSH 端口", "placeholder": "22"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "username", "label": "SSH 用户名", "placeholder": "admin"}
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "password", "label": "SSH 密码", "type": "password"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "interval_hours", "label": "轮询间隔(小时)", "placeholder": "12"}
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "stop_threshold_gb", "label": "停止下载阈值(GB)", "placeholder": "500"}
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "resume_threshold_gb", "label": "恢复下载阈值(GB)", "placeholder": "2000"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {"model": "auto_pause_download", "label": "低于阈值时自动暂停下载"}
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {"model": "monitor_all", "label": "监控全部存储池（默认仅 CACHEDEV 数据卷）"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VAlert",
                        "props": {
                            "type": "info",
                            "variant": "tonal",
                            "text": "低于「停止下载阈值」时暂停下载器所有正在下载的任务（保留做种/上传）；高于「恢复下载阈值」时自动恢复。仅支持 Transmission 下载器。"
                        }
                    }
                ]
            }
        ], {
            "enabled": False,
            "host": "192.168.1.11",
            "port": 22,
            "username": "",
            "password": "",
            "interval_hours": 12,
            "stop_threshold_gb": 500,
            "resume_threshold_gb": 2000,
            "auto_pause_download": True,
            "monitor_all": False,
            "onlyonce": False
        }

    def get_page(self) -> Optional[List[dict]]:
        """返回插件详情页面，展示最近一次检查结果与下载暂停状态。"""
        if not self._enabled:
            return None
        last_report = self.get_data("last_report")
        paused = self._download_paused
        lines = []
        lines.append(f"下载任务状态：{'已暂停（等待容量恢复）' if paused else '正常'}")
        if last_report:
            lines.append(str(last_report))
        return [{
            "component": "VAlert",
            "props": {"type": "info", "text": "\n".join(lines)}
        }]

    def stop_service(self) -> None:
        """停止插件后台服务并释放资源。"""
        return None

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
        elif avail_gb > self._resume_threshold_gb and self._download_paused:
            # 高于恢复阈值：恢复下载
            if self._resume_downloads():
                self._download_paused = False
                self.save_data("download_paused", False)
                text = (
                    f"存储池 {min_name} 剩余 {avail_gb:.0f}G，已高于恢复阈值 "
                    f"{self._resume_threshold_gb:.0f}G，已自动恢复下载任务。\n\n"
                    + "\n".join(lines)
                )
                self._notify("QNAP 存储池恢复：已恢复下载", text)
            else:
                self._notify(
                    "QNAP 存储池恢复：恢复下载失败",
                    f"存储池 {min_name} 剩余 {avail_gb:.0f}G 已高于恢复阈值，"
                    f"但恢复下载任务失败，请手动处理。"
                )
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
            if not host or not port:
                logger.warning("QNAP存储池监控：Transmission 配置缺少 host/port")
                continue
            client = Transmission(
                host=str(host),
                port=int(port),
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
