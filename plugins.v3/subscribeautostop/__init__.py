"""订阅入库自停插件入口。

定时扫描「订阅中(R)」的订阅，判断其媒体是否已完整入库：
- 电影：整部已入库即命中；
- 电视剧：目标季整季集数全齐才命中（缺集、未填总集数均不判定，避免误停）；
- 命中后按配置执行「暂停(state=S)」或「删除」。

本文件负责与 MoviePilot 插件框架对接（元数据、配置装载、定时服务注册、
API 端点），核心扫描逻辑在 ``core`` 中实现。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.triggers.cron import CronTrigger

from app.chain.base import ChainBase
from app.db.oper.subscribe import SubscribeOper
from app.plugins import _PluginBase
from app.schemas.context import MediaInfo
from app.schemas.types import MediaType
from app.sdk.logging import logger

from .core.scanner import ScanReport, SubscriptionAutoStopScanner


class SubscribeAutoStop(_PluginBase):
    """订阅入库自停插件（Vue 联邦渲染）。"""

    plugin_name = "订阅入库自停"
    plugin_desc = "定时扫描订阅中的影片是否已完整入库，命中后自动暂停或删除对应订阅，避免重复下载。"
    plugin_icon = "subscribeautostop.png"
    plugin_version = "1.0.0"
    plugin_author = "local"
    author_url = None
    plugin_config_prefix = "subscribeautostop_"
    plugin_order = 30
    auth_level = 1

    DEFAULT_CRON = "0 3 * * *"

    def __init__(self):
        """初始化插件实例状态。"""
        super().__init__()
        self._enabled: bool = False
        self._cron: str = self.DEFAULT_CRON
        self._action: str = "pause"  # pause / delete
        self._notify: bool = False
        self._last_report: Optional[ScanReport] = None

    def init_plugin(self, config: dict = None) -> None:
        """根据插件配置初始化运行状态。

        :param config: 持久化保存的插件配置字典。
        """
        self.stop_service()
        self._enabled = False
        self._cron = self.DEFAULT_CRON
        self._action = "pause"
        self._notify = False
        if config:
            self._enabled = bool(config.get("enabled"))
            cron = str(config.get("cron") or "").strip()
            if cron:
                self._cron = cron
            action = str(config.get("action") or "pause").strip().lower()
            self._action = action if action in ("pause", "delete") else "pause"
            self._notify = bool(config.get("notify"))

    def get_state(self) -> bool:
        """获取插件启用状态。

        :return: 是否启用。
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。

        :return: 命令定义列表，本插件未提供命令。
        """
        return []

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件使用 Vue 联邦组件渲染。

        :return: 渲染模式与资源目录元组。
        """
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """返回插件默认配置（Vue 模式下表单由远程 Config 组件渲染）。

        :return: 空表单与默认配置字典。
        """
        return [], {
            "enabled": False,
            "cron": self.DEFAULT_CRON,
            "action": "pause",
            "notify": False,
        }

    def get_page(self) -> Optional[List[Dict[str, Any]]]:
        """返回插件详情页面（Vue 模式下由远程 Page 组件渲染）。

        :return: 空列表。
        """
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        """注册插件定时服务。

        :return: 定时服务定义列表。
        """
        if not self._enabled:
            return []
        return [
            {
                "id": "SubscribeAutoStop",
                "name": "订阅入库自停扫描",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.scan_now,
                "kwargs": {},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表。

        :return: API 端点定义列表。
        """
        return [
            {
                "path": "/scan",
                "endpoint": self.api_scan,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即扫描一次订阅入库状态",
            },
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "查看最近一次扫描结果",
            },
        ]

    def stop_service(self) -> None:
        """停止插件后台服务并释放资源。"""
        return None

    # ------------------------------------------------------------------
    # 扫描与判定
    # ------------------------------------------------------------------

    def scan_now(self) -> ScanReport:
        """执行一次完整扫描：遍历订阅中的订阅并判定是否已入库。

        :return: 本次扫描报告。
        """
        logger.info("订阅入库自停：开始扫描订阅入库状态")
        report = self._build_scanner().run()
        self._last_report = report
        logger.info(
            "订阅入库自停：扫描完成，命中 %d 条，已处理 %d 条",
            report.hit_count,
            report.processed_count,
        )
        if self._notify and report.hit_count:
            self.post_message(
                title="订阅入库自停",
                text=self._format_notify_text(report),
            )
        return report

    def _build_scanner(self) -> "SubscriptionAutoStopScanner":
        """构造扫描器实例。

        :return: 配置好的扫描器。
        """
        return SubscriptionAutoStopScanner(
            subscribe_oper=SubscribeOper(),
            media_chain=ChainBase(),
            action=self._action,
        )

    def _format_notify_text(self, report: ScanReport) -> str:
        """格式化通知文本。

        :param report: 扫描报告。
        :return: 通知正文。
        """
        lines = [f"本次扫描命中 {report.hit_count} 条已入库订阅："]
        for item in report.hits:
            verb = "已暂停" if item.action == "pause" else "已删除"
            lines.append(f"- {item.name}（{verb}）")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # API 端点
    # ------------------------------------------------------------------

    def api_status(self) -> Dict[str, Any]:
        """返回插件最近扫描状态。

        :return: 插件状态与最近扫描报告。
        """
        report = self._last_report
        return {
            "success": True,
            "data": {
                "enabled": self._enabled,
                "cron": self._cron,
                "action": self._action,
                "notify": self._notify,
                "last_report": report.to_dict() if report else None,
            },
        }

    def api_scan(self) -> Dict[str, Any]:
        """立即触发一次扫描并返回结果。

        :return: 本次扫描报告。
        """
        report = self.scan_now()
        return {"success": True, "data": report.to_dict()}
