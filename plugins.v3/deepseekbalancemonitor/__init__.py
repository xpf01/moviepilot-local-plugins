"""DeepSeek 账户余额监控插件。

定时调用 DeepSeek 官方开放平台的 ``GET /user/balance`` 接口，读取账户的可用余额。
当总可用余额（充值余额 + 赠金）低于配置的告警阈值、或账户因欠费不可用时，
通过 MoviePilot 通知渠道推送告警；告警采用「状态去重」——从欠费/低余额状态恢复后，
下一轮再次跌破阈值才会重新告警，避免周期性重复骚扰。

余额查询复用 MoviePilot 已配置的 LLM 接口凭据（``LLM_API_KEY`` / ``LLM_BASE_URL``），
无需单独填写密钥；当 ``LLM_BASE_URL`` 非官方地址时也可通过配置里的自定义接口覆盖。
使用 httpx 发送请求，不额外引入第三方依赖。
"""

from typing import Any, Dict, List, Optional, Tuple

import httpx
from apscheduler.triggers.interval import IntervalTrigger

from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.runtime.config import settings
from app.sdk.logging import logger


class DeepSeekBalanceMonitor(_PluginBase):
    """DeepSeek 账户余额监控插件。"""

    plugin_name = "DeepSeek余额监控"
    plugin_desc = "定时查询 DeepSeek 账户余额（充值/赠金/总额），低于阈值或欠费时通知告警，充值恢复后再次触发。"
    plugin_icon = "deepseekbalancemonitor.png"
    plugin_version = "1.0.0"
    plugin_label = "系统工具,监控,DeepSeek"
    plugin_author = "local"
    plugin_config_prefix = "deepseekbalancemonitor_"
    plugin_order = 31
    auth_level = 1

    # 官方充值页与用量看板跳转地址（消费/请求次数/Token 用量官方无 API，仅后台可见）
    TOP_UP_URL = "https://platform.deepseek.com/top_up"
    USAGE_URL = "https://platform.deepseek.com/usage"

    _enabled = False
    _interval_minutes = 60
    _threshold = 5.0
    _api_key = ""
    _base_url = "https://api.deepseek.com"
    _balance_url = "https://api.deepseek.com/user/balance"
    _timeout = 20
    _use_proxy = False
    _onlyonce = False

    # 告警去重状态标记，落入插件数据，重启后仍保留「已告警」状态，避免重启后重复告警
    _alerted = False

    def init_plugin(self, config: dict = None) -> None:
        """根据插件配置初始化运行状态。

        :param config: 插件配置字典。
        """
        self.stop_service()
        self._enabled = False
        if not config:
            return
        self._enabled = bool(config.get("enabled"))
        self._interval_minutes = int(config.get("interval_minutes") or 60)
        self._threshold = float(config.get("threshold") or 5.0)
        # 优先用配置里显式填写的 Key / 余额接口，空值则回退到 MoviePilot 全局 LLM 配置
        self._api_key = str(config.get("api_key") or "").strip() or (settings.LLM_API_KEY or "")
        self._base_url = str(config.get("base_url") or "").strip() or (settings.LLM_BASE_URL or "https://api.deepseek.com")
        self._balance_url = str(config.get("balance_url") or "").strip() or f"{self._base_url.rstrip('/')}/user/balance"
        self._timeout = int(config.get("timeout") or 20)
        self._use_proxy = bool(config.get("use_proxy"))
        self._onlyonce = bool(config.get("onlyonce"))
        # 恢复上次的告警状态，保证重启后仍不重复告警
        self._alerted = bool(self.get_data("alerted"))
        if self._enabled and self._onlyonce:
            import threading
            threading.Thread(target=self._check_and_notify, daemon=True).start()

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def get_service(self) -> List[Dict[str, Any]]:
        """注册插件定时服务，按配置周期查询 DeepSeek 余额。"""
        if not self._enabled:
            return []
        return [{
            "id": "DeepSeekBalanceMonitor",
            "name": "DeepSeek余额监控",
            "trigger": IntervalTrigger(minutes=self._interval_minutes),
            "func": self._check_and_notify,
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
                "summary": "查看最近余额检查结果与告警状态",
            },
            {
                "path": "/check_now",
                "endpoint": self.api_check_now,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即执行一次余额检查",
            },
        ]

    def api_status(self) -> Dict[str, Any]:
        """返回插件运行状态摘要，供 Vue 详情页展示。

        :return: 包含启用状态、最近余额明细、告警状态与充值/看板跳转地址的字典。
        """
        return {
            "success": True,
            "data": {
                "enabled": self._enabled,
                "alerted": self._alerted,
                "threshold": self._threshold,
                "last_report": self.get_data("last_report") or "",
                "balance": self.get_data("last_balance") or {},
                "top_up_url": self.TOP_UP_URL,
                "usage_url": self.USAGE_URL,
            },
        }

    def api_check_now(self) -> Dict[str, Any]:
        """立即执行一次余额检查，供 Vue 详情页触发。

        :return: 检查完成后的状态摘要。
        """
        if not self._enabled:
            return {"success": False, "message": "插件未启用"}
        self._check_and_notify()
        return {
            "success": True,
            "message": "检查完成",
            "data": {
                "alerted": self._alerted,
                "threshold": self._threshold,
                "last_report": self.get_data("last_report") or "",
                "balance": self.get_data("last_balance") or {},
                "top_up_url": self.TOP_UP_URL,
                "usage_url": self.USAGE_URL,
            },
        }

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回插件默认配置（Vue 模式下表单由远程 Config 组件渲染）。"""
        return [], {
            "enabled": False,
            "interval_minutes": 60,
            "threshold": 5.0,
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "balance_url": "",
            "timeout": 20,
            "use_proxy": False,
            "onlyonce": False,
        }

    def get_page(self) -> Optional[List[dict]]:
        """返回插件详情页面（Vue 模式下由远程 Page 组件渲染）。"""
        return []

    def stop_service(self) -> None:
        """停止插件后台服务并释放资源。"""
        return None

    def _check_and_notify(self) -> None:
        """执行一次余额查询，并按阈值与去重状态决定是否告警。"""
        if not self._api_key:
            logger.warning("DeepSeek余额监控：未配置 API Key，跳过检查")
            self._notify("DeepSeek 余额监控", "未配置 DeepSeek API Key，请在插件配置或系统 LLM 设置中填写。")
            return

        data = self._query_balance()
        if data is None:
            logger.error("DeepSeek余额监控：余额查询失败")
            self._notify("DeepSeek 余额监控", "余额查询失败，请检查 API Key 与网络连接。")
            return

        is_available = bool(data.get("is_available"))
        infos = data.get("balance_infos") or []
        # 汇总各币种（通常只有 CNY 一项），取总可用余额之和
        total = 0.0
        currency = ""
        topped_up = 0.0
        granted = 0.0
        for info in infos:
            try:
                total += float(info.get("total_balance") or 0)
            except (TypeError, ValueError):
                pass
            try:
                topped_up += float(info.get("topped_up_balance") or 0)
            except (TypeError, ValueError):
                pass
            try:
                granted += float(info.get("granted_balance") or 0)
            except (TypeError, ValueError):
                pass
            if not currency and info.get("currency"):
                currency = str(info["currency"])

        report = (
            f"总余额 {total:.4f} {currency}（充值 {topped_up:.4f} + 赠金 {granted:.4f}），"
            f"账户{'可用' if is_available else '不可用'}"
        )
        self.save_data("last_report", report)
        # 结构化余额明细，供 Vue 详情页展示充值/赠金/总额与跳转
        self.save_data("last_balance", {
            "currency": currency,
            "total_balance": total,
            "topped_up_balance": topped_up,
            "granted_balance": granted,
            "is_available": is_available,
        })
        logger.info("DeepSeek余额监控检查完成：%s", report)

        # 欠费停摆：账户不可用，无条件告警（即使已告警也保留状态，恢复前不重复）
        if not is_available:
            if not self._alerted:
                self._alerted = True
                self.save_data("alerted", True)
                self._notify(
                    "DeepSeek 余额告警：账户不可用",
                    f"DeepSeek 账户已不可用（is_available=false），Agent 可能无法调用模型。\n\n{report}"
                )
            return

        # 低于阈值：告警一次，充值回升后才重置去重标记
        if total < self._threshold:
            if not self._alerted:
                self._alerted = True
                self.save_data("alerted", True)
                self._notify(
                    "DeepSeek 余额告警：余额不足",
                    f"DeepSeek 可用余额 {total:.4f} {currency} 已低于阈值 {self._threshold}，"
                    f"请及时充值以免 Agent 因欠费停摆。\n\n{report}"
                )
        else:
            # 余额充足：若此前处于告警状态，说明已充值恢复，重置去重标记并提示
            if self._alerted:
                self._alerted = False
                self.save_data("alerted", False)
                self._notify(
                    "DeepSeek 余额恢复",
                    f"DeepSeek 可用余额已恢复至 {total:.4f} {currency}，高于阈值 {self._threshold}。\n\n{report}"
                )

    def _query_balance(self) -> Optional[Dict[str, Any]]:
        """调用 DeepSeek ``/user/balance`` 接口读取余额。

        :return: 余额响应字典；请求或解析失败返回 None。
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=self._timeout, trust_env=self._use_proxy) as client:
                resp = client.get(self._balance_url, headers=headers)
                resp.raise_for_status()
                payload = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("DeepSeek余额监控：接口返回 %s，%s", exc.response.status_code, exc.response.text[:200])
            return None
        except Exception as exc:  # pragma: no cover
            logger.error("DeepSeek余额监控：请求失败 %s", exc)
            return None

        if not isinstance(payload, dict):
            logger.error("DeepSeek余额监控：接口返回非预期结构 %s", type(payload))
            return None
        return payload

    def _notify(self, title: str, text: str) -> None:
        """通过 MoviePilot 通知渠道推送消息。

        :param title: 通知标题。
        :param text: 通知正文。
        """
        try:
            self.post_message(mtype=NotificationType.Plugin, title=title, text=text)
        except Exception as exc:  # pragma: no cover
            logger.error("DeepSeek余额监控：发送通知失败 %s", exc)
