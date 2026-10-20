"""ISO 蓝光原盘自动转封装插件。

扫描影视下载目录中的 ``.iso`` 单文件，挂载后定位主视频（BDMV/STREAM 下最大的
``.m2ts``），使用 ffmpeg 无损转封装为单个 MKV 并输出到同目录，交由 MoviePilot
原生整理流程硬链接入库。原始 ISO 保留不动，按「绝对路径+文件大小」去重，避免
重复处理。
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger
from app.sdk.scheduler import add_plugin_once_job


class IsoRemuxOrganize(_PluginBase):
    """ISO 原盘转封装插件。"""

    plugin_name = "ISO原盘转封装"
    plugin_desc = "自动扫描影视下载目录中的蓝光原盘 ISO，挂载后无损转封装为 MKV 入库。"
    plugin_icon = "isoremuxorganize.png"
    plugin_version = "1.0.0"
    plugin_label = "文件整理,蓝光原盘,ffmpeg,ISO"
    plugin_author = "local"
    plugin_config_prefix = "isoremuxorganize_"
    plugin_order = 60
    auth_level = 1

    # 扫描根目录默认值（影视下载目录）
    _DEFAULT_SCAN_ROOT = "/media/影视下载"
    # 定时扫描间隔（秒）
    _DEFAULT_INTERVAL = 1800
    # 一次性任务延迟（秒），事件触发后等待文件落盘稳定
    _EVENT_DELAY = 60
    # 去重记录 key
    _DATA_KEY = "processed"
    # 处理中锁，避免并发重复处理同一文件
    _processing: set = set()

    _enabled = False
    _scan_root = _DEFAULT_SCAN_ROOT
    _interval = _DEFAULT_INTERVAL
    _notify = True
    _ffmpeg_timeout = 21600

    def init_plugin(self, config: Optional[Dict[str, Any]] = None) -> None:
        """根据插件配置初始化运行状态。"""
        self.stop_service()
        self._enabled = False
        self._scan_root = self._DEFAULT_SCAN_ROOT
        self._interval = self._DEFAULT_INTERVAL
        self._notify = True
        self._ffmpeg_timeout = 21600
        if not config:
            return
        self._enabled = bool(config.get("enabled"))
        scan_root = str(config.get("scan_root") or "").strip()
        if scan_root:
            self._scan_root = scan_root
        try:
            self._interval = int(config.get("interval") or self._DEFAULT_INTERVAL)
        except (TypeError, ValueError):
            self._interval = self._DEFAULT_INTERVAL
        self._notify = bool(config.get("notify", True))
        try:
            self._ffmpeg_timeout = int(config.get("timeout") or 21600)
        except (TypeError, ValueError):
            self._ffmpeg_timeout = 21600
        if self._enabled:
            # 启动时安排一次延迟首扫，并进入自递归定时扫描
            add_plugin_once_job(
                self.__class__.__name__,
                "initial_scan",
                self._scan_job,
                "ISO原盘转封装首扫",
                delay_seconds=30,
            )

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表。"""
        return []

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
                            "model": "scan_root",
                            "label": "扫描根目录",
                            "placeholder": "/media/影视下载",
                        },
                    },
                    {
                        "component": "VTextField",
                        "props": {
                            "model": "interval",
                            "label": "定时扫描间隔（秒）",
                            "type": "number",
                            "min": 300,
                            "placeholder": "1800",
                        },
                    },
                    {
                        "component": "VTextField",
                        "props": {
                            "model": "timeout",
                            "label": "转封装超时（秒）",
                            "type": "number",
                            "min": 60,
                            "placeholder": "21600",
                        },
                    },
                    {
                        "component": "VSwitch",
                        "props": {"model": "notify", "label": "处理完成发送通知"},
                    },
                    {
                        "component": "VAlert",
                        "props": {
                            "type": "info",
                            "variant": "tonal",
                            "text": "仅处理 .iso 单文件；挂载后定位最大 m2ts 无损转 MKV，原始 ISO 保留。",
                        },
                    },
                ],
            }
        ], {
            "enabled": False,
            "scan_root": self._DEFAULT_SCAN_ROOT,
            "interval": self._DEFAULT_INTERVAL,
            "timeout": 21600,
            "notify": True,
        }

    def get_page(self) -> Optional[List[Dict[str, Any]]]:
        """返回插件详情页面。"""
        return None

    def stop_service(self) -> None:
        """停止插件后台任务。"""
        return None

    # ------------------------------------------------------------------ 事件

    @eventmanager.register(EventType.TransferComplete)
    def on_transfer_complete(self, event: Event) -> None:
        """整理完成事件触发延迟扫描。"""
        self._schedule_deferred_scan()

    @eventmanager.register(EventType.DownloadAdded)
    def on_download_added(self, event: Event) -> None:
        """下载添加事件触发延迟扫描。"""
        self._schedule_deferred_scan()

    def _schedule_deferred_scan(self) -> None:
        """延迟一段时间后触发一次扫描，避免新文件尚未落盘稳定。"""
        if not self._enabled:
            return
        add_plugin_once_job(
            self.__class__.__name__,
            "deferred_scan",
            self._scan_job,
            "ISO原盘转封装事件扫描",
            delay_seconds=self._EVENT_DELAY,
        )

    # ------------------------------------------------------------------ 扫描

    def _scan_job(self) -> None:
        """执行一次扫描，并在结束后安排下一次定时扫描。"""
        if not self._enabled:
            return
        try:
            self._scan_and_process()
        except Exception as exc:  # noqa: BLE001 - 扫描任务不得中断自递归调度
            logger.error(f"扫描过程中发生异常：{exc}")
        finally:
            # 自递归：排下一个定时扫描任务
            add_plugin_once_job(
                self.__class__.__name__,
                "periodic_scan",
                self._scan_job,
                "ISO原盘转封装定时扫描",
                delay_seconds=self._interval,
            )

    def _scan_and_process(self) -> None:
        """扫描根目录下的所有 ``.iso`` 文件并逐个处理未去重项。"""
        root = Path(self._scan_root)
        if not root.is_dir():
            logger.warn(f"扫描根目录不存在：{root}")
            return
        iso_files = sorted(root.rglob("*.iso"))
        if not iso_files:
            logger.info("未发现 ISO 文件")
            return
        for iso_path in iso_files:
            if str(iso_path) in self._processing:
                continue
            if self._is_processed(iso_path):
                continue
            self._processing.add(str(iso_path))
            try:
                self._process_iso(iso_path)
            except Exception as exc:  # noqa: BLE001 - 单个文件失败不影响后续
                logger.warn(f"处理 ISO 失败 {iso_path}：{exc}")
            finally:
                self._processing.discard(str(iso_path))

    # ------------------------------------------------------------------ 去重

    def _file_key(self, iso_path: Path) -> str:
        """根据绝对路径与文件大小生成去重键。"""
        try:
            size = iso_path.stat().st_size
        except OSError:
            size = -1
        raw = f"{str(iso_path)}|{size}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _is_processed(self, iso_path: Path) -> bool:
        """判断指定 ISO 是否已处理过。"""
        data = self.get_data(self._DATA_KEY) or {}
        return self._file_key(iso_path) in data

    def _mark_processed(self, iso_path: Path) -> None:
        """记录指定 ISO 已处理。"""
        data = self.get_data(self._DATA_KEY) or {}
        data[self._file_key(iso_path)] = {
            "path": str(iso_path),
            "size": iso_path.stat().st_size,
        }
        self.save_data(self._DATA_KEY, data)

    # ------------------------------------------------------------------ 处理

    def _process_iso(self, iso_path: Path) -> None:
        """挂载 ISO、定位主视频、无损转 MKV、卸载。"""
        logger.info(f"开始处理 ISO：{iso_path}")
        # 若同目录已存在同名且大小合理的 MKV，视为已转封装过，直接记录跳过
        out_mkv = iso_path.with_suffix(".mkv")
        try:
            if out_mkv.exists() and out_mkv.stat().st_size >= 10 * 1024 * 1024:
                self._mark_processed(iso_path)
                logger.info(f"同名 MKV 已存在，跳过转封装：{out_mkv}")
                return
        except OSError:
            pass
        mount_dir = self._mount_iso(iso_path)
        if mount_dir is None:
            logger.warn(f"挂载失败，跳过：{iso_path}")
            return
        try:
            m2ts = self._find_main_m2ts(mount_dir)
            if m2ts is None:
                logger.warn(f"未定位到主视频 m2ts，跳过：{iso_path}")
                return
            if self._remux(m2ts, out_mkv):
                self._mark_processed(iso_path)
                logger.info(f"转封装完成：{out_mkv}")
                if self._notify:
                    self.post_message(
                        mtype=None,
                        title="ISO 原盘转封装完成",
                        text=f"{iso_path.name} 已转封装为 {out_mkv.name}",
                    )
        finally:
            self._umount(mount_dir)

    def _mount_iso(self, iso_path: Path) -> Optional[Path]:
        """只读 loop 挂载 ISO，返回挂载目录；失败返回 None。"""
        mount_dir = Path(tempfile.mkdtemp(prefix="iso_remux_"))
        cmd = ["mount", "-o", "loop,ro", str(iso_path), str(mount_dir)]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warn(f"挂载命令执行失败：{exc}")
            mount_dir.rmdir(ignore_errors=True)
            return None
        if result.returncode != 0:
            logger.warn(f"挂载失败：{result.stderr.decode(errors='replace')}")
            mount_dir.rmdir(ignore_errors=True)
            return None
        return mount_dir

    def _umount(self, mount_dir: Path) -> None:
        """卸载挂载点并清理目录。"""
        subprocess.run(["umount", str(mount_dir)], capture_output=True, timeout=30)
        shutil.rmtree(mount_dir, ignore_errors=True)

    @staticmethod
    def _find_main_m2ts(mount_dir: Path) -> Optional[Path]:
        """在 BDMV/STREAM 下返回体积最大的 m2ts 作为主视频。"""
        stream_dir = mount_dir / "BDMV" / "STREAM"
        if not stream_dir.is_dir():
            return None
        m2ts_files = [p for p in stream_dir.iterdir() if p.suffix.lower() == ".m2ts"]
        if not m2ts_files:
            return None
        return max(m2ts_files, key=lambda p: p.stat().st_size)

    def _remux(self, m2ts: Path, out_mkv: Path) -> bool:
        """使用 ffmpeg 无损转封装 m2ts 为 MKV，丢弃 PGS 图形字幕。"""
        if out_mkv.exists():
            out_mkv.unlink()
        cmd = [
            "ffmpeg", "-y",
            "-i", str(m2ts),
            "-map", "0",
            "-c", "copy",
            "-sn",
            str(out_mkv),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self._ffmpeg_timeout,
            )
        except subprocess.TimeoutExpired:
            logger.warn(f"ffmpeg 转封装超时：{out_mkv}")
            return False
        if result.returncode != 0:
            logger.warn(
                f"ffmpeg 转封装失败：{result.stderr.decode(errors='replace')[-500:]}"
            )
            return False
        return out_mkv.exists() and out_mkv.stat().st_size > 0
