"""馒头（M-Team）每日自动登录保活插件。

站点账号规则明确：连续 40 天未「用浏览器存取网站网页」将被删号，且
「单纯做种不算登录，使用第三方工具间接存取也不算登录」。同时站点 API
使用规范禁止第三方调用 ``/login`` 前缀的端点，因此唯一合规且有效的保活
方式是每天用真实浏览器打开网页完成一次存取。

站点自 2026 年起强制登入验证码，且「每台设备仅需首次输入一次，有效期 30 天」。
因此插件使用**持久化浏览器配置目录**保存设备受信状态：日常运行时浏览器仍被
站点视为同一台设备，无需每次验证；仅当 30 天有效期到期时，插件自动点击
「获取验证码」把验证码发到注册邮箱，并通过通知请使用者手动填入一次。

用户名、密码与邮箱由使用者在插件配置界面自行填写，插件不会输出或记录明文凭据。
"""

import hashlib
import hmac
import shutil
import struct
import threading
import time
from base64 import b32decode
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pytz
from apscheduler.triggers.cron import CronTrigger

from app.db.site_oper import SiteOper
from app.plugins import _PluginBase
from app.runtime.settings import get_runtime_setting
from app.sdk.logging import logger
from app.sdk.network import RequestUtils


class MTeamAutoLogin(_PluginBase):
    """馒头每日自动登录保活插件（Vue 联邦渲染）。"""

    plugin_name = "馒头自动登录保活"
    plugin_desc = (
        "每天用真实浏览器存取馒头网页保活（站点不认 API 访问）；设备受信 30 天到期时"
        "自动发邮箱验证码并通知手动填入。"
    )
    plugin_icon = "mteamautologin.png"
    plugin_version = "1.3.1"
    plugin_label = "站点"
    plugin_author = "local"
    author_url = None
    plugin_config_prefix = "mteamautologin_"
    plugin_order = 99
    auth_level = 1

    # 默认执行周期：每天 08:17（避开整点任务高峰）
    DEFAULT_CRON = "17 8 * * *"
    # 默认登录页与站点首页
    DEFAULT_LOGIN_URL = "https://kp.m-team.cc/login"
    DEFAULT_HOME_URL = "https://kp.m-team.cc/"
    # 登录表单阶段的等待上限（秒）
    LOGIN_TIMEOUT = 60
    # 邮箱验证码等待上限默认值（秒）
    DEFAULT_CODE_WAIT = 600
    # 验证码需要补填时的默认重试间隔（分钟）与次数
    DEFAULT_RETRY_INTERVAL = 20
    DEFAULT_RETRY_TIMES = 3
    # 站点设备受信有效期（天）
    DEVICE_VALID_DAYS = 30
    # 提前提醒补码的天数阈值
    DEVICE_WARN_DAYS = 29
    # 保活期限（天）
    KEEPALIVE_DAYS = 40
    # 历史保留条数
    HISTORY_LIMIT = 20
    # 页面元素标记属性
    _PICK = "[data-mp-pick='1']"

    def __init__(self) -> None:
        """初始化插件实例状态。"""
        super().__init__()
        self._enabled: bool = False
        self._cron: str = self.DEFAULT_CRON
        self._login_url: str = self.DEFAULT_LOGIN_URL
        self._home_url: str = self.DEFAULT_HOME_URL
        self._username: str = ""
        self._password: str = ""
        self._email: str = ""
        self._totp_secret: str = ""
        self._notify_success: bool = False
        self._use_proxy: bool = False
        self._code_wait: int = self.DEFAULT_CODE_WAIT
        self._retry_interval: int = self.DEFAULT_RETRY_INTERVAL
        self._retry_times: int = self.DEFAULT_RETRY_TIMES
        self._onlyonce: bool = False
        self._last_result: Dict[str, Any] = {}
        # 串行化登录执行，避免定时任务与手动触发并发抢占浏览器实例
        self._run_lock = threading.Lock()
        # 手动补码通道：等待中的浏览器与页面提交的验证码
        self._code_event = threading.Event()
        self._pending_code: str = ""
        self._awaiting_code: bool = False
        self._code_requested_at: str = ""
        self._code_deadline: str = ""

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def init_plugin(self, config: dict = None) -> None:
        """根据插件配置初始化运行状态。

        :param config: 持久化保存的插件配置字典。
        """
        self.stop_service()
        self._enabled = False
        self._cron = self.DEFAULT_CRON
        self._login_url = self.DEFAULT_LOGIN_URL
        self._home_url = self.DEFAULT_HOME_URL
        self._username = ""
        self._password = ""
        self._email = ""
        self._totp_secret = ""
        self._notify_success = False
        self._use_proxy = False
        self._code_wait = self.DEFAULT_CODE_WAIT
        self._retry_interval = self.DEFAULT_RETRY_INTERVAL
        self._retry_times = self.DEFAULT_RETRY_TIMES
        self._onlyonce = False
        self._last_result = {}
        if config:
            self._enabled = bool(config.get("enabled"))
            cron = str(config.get("cron") or "").strip()
            self._cron = cron if cron.count(" ") == 4 else self.DEFAULT_CRON
            self._login_url = str(config.get("login_url") or "").strip() or self.DEFAULT_LOGIN_URL
            self._home_url = str(config.get("home_url") or "").strip() or self.DEFAULT_HOME_URL
            self._username = str(config.get("username") or "").strip()
            # 密码保持原样，不做 strip，避免误伤首尾含空格的密码
            self._password = str(config.get("password") or "")
            self._email = str(config.get("email") or "").strip()
            self._totp_secret = str(config.get("totp_secret") or "").replace(" ", "")
            self._notify_success = bool(config.get("notify_success"))
            self._use_proxy = bool(config.get("use_proxy"))
            self._code_wait = self._positive_int(config.get("code_wait"), self.DEFAULT_CODE_WAIT)
            self._retry_interval = self._positive_int(
                config.get("retry_interval"), self.DEFAULT_RETRY_INTERVAL
            )
            self._retry_times = self._positive_int(
                config.get("retry_times"), self.DEFAULT_RETRY_TIMES, allow_zero=True
            )
            self._onlyonce = bool(config.get("onlyonce"))
            self._last_result = dict(config.get("last_result") or {})

        if self._enabled and self._onlyonce:
            self._onlyonce = False
            self.update_config(self._current_config())
            logger.info("馒头自动登录：配置为立即执行一次，稍后开始登录")
            self._start_thread(self.run_login)

    @staticmethod
    def _positive_int(value: Any, default: int, allow_zero: bool = False) -> int:
        """把配置值转为非负整数，非法时退回默认值。

        :param value: 原始配置值。
        :param default: 非法时使用的默认值。
        :param allow_zero: 是否允许 0。
        :return: 规范化后的整数。
        """
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        if number < 0 or (number == 0 and not allow_zero):
            return default
        return number

    def get_state(self) -> bool:
        """获取插件启用状态。

        :return: 是否启用。
        """
        return self._enabled

    def stop_service(self) -> None:
        """停止插件后台服务并释放资源。"""
        return None

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。

        :return: 空列表，本插件不提供远程命令。
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
        return [], self._current_config()

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
        try:
            trigger = CronTrigger.from_crontab(self._cron)
        except Exception as err:  # noqa: BLE001 - 非法表达式降级为不注册
            logger.error(f"馒头自动登录：定时表达式异常，已跳过注册：{err}")
            return []
        return [
            {
                "id": "MTeamAutoLogin",
                "name": "馒头每日自动登录保活",
                "trigger": trigger,
                "func": self.run_login,
                "kwargs": {},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API 列表。

        :return: API 端点定义列表。
        """
        return [
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "读取登录保活状态",
            },
            {
                "path": "/login",
                "endpoint": self.api_login,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即用浏览器登录一次馒头",
            },
            {
                "path": "/code",
                "endpoint": self.api_code,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "提交邮箱验证码，继续等待中的登录",
            },
            {
                "path": "/reverify",
                "endpoint": self.api_reverify,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清空浏览器设备身份并重新验证（重置 30 天）",
            },
        ]

    # ------------------------------------------------------------------
    # 插件 API
    # ------------------------------------------------------------------

    def api_status(self) -> Dict[str, Any]:
        """返回插件状态、待补码信息与最近登录记录。

        :return: 前端展示用的状态字典。
        """
        history = self.get_data("login_history") or []
        days_since = self._device_days_since()
        return {
            "enabled": self._enabled,
            "cron": self._cron,
            "login_url": self._login_url,
            "home_url": self._home_url,
            "username": self._username,
            "has_password": bool(self._password),
            "email": self._email,
            "has_totp": bool(self._totp_secret),
            "notify_success": self._notify_success,
            "use_proxy": self._use_proxy,
            "code_wait": self._code_wait,
            "retry_interval": self._retry_interval,
            "retry_times": self._retry_times,
            "keepalive_days": self.KEEPALIVE_DAYS,
            "device_valid_days": self.DEVICE_VALID_DAYS,
            "device_verified_at": self.get_data("device_verified_at") or "",
            "device_days_since": days_since,
            "device_expire_in": (self.DEVICE_VALID_DAYS - days_since) if days_since is not None else None,
            "awaiting_code": self._awaiting_code,
            "code_requested_at": self._code_requested_at,
            "code_deadline": self._code_deadline,
            "last_result": self._public_result(self._last_result),
            "history": [self._public_result(item) for item in history[: self.HISTORY_LIMIT]],
            "next_run": self._next_run_text(),
        }

    def api_login(self) -> Dict[str, Any]:
        """手动触发一次浏览器登录。

        :return: 触发结果提示。
        """
        if not self._enabled:
            return {"success": False, "message": "插件未启用"}
        if not self._username or not self._password:
            return {"success": False, "message": "请先在插件配置中填写馒头用户名与密码"}
        if self._run_lock.locked():
            return {"success": False, "message": "已有一次登录正在执行，请稍后再试"}
        self._start_thread(self.run_login)
        return {"success": True, "message": "已开始登录，如需要验证码会自动发信并提示"}

    def api_code(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """接收使用者提交的邮箱验证码，交给等待中的浏览器提交。

        :param payload: 请求体，含 code 字段。
        :return: 提交结果提示。
        """
        payload = payload or {}
        code = str(payload.get("code") or "").strip().replace(" ", "")
        if not code:
            return {"success": False, "message": "请输入收到的验证码"}
        if not self._awaiting_code:
            return {
                "success": False,
                "message": "当前没有等待验证码的登录，请先点「立即登录」重新获取验证码",
            }
        self._pending_code = code
        self._code_event.set()
        return {"success": True, "message": "验证码已提交，正在完成登录"}

    def api_reverify(self) -> Dict[str, Any]:
        """清空浏览器设备身份并重新走一次登录验证。

        :return: 触发结果提示。
        """
        if not self._enabled:
            return {"success": False, "message": "插件未启用"}
        if not self._username or not self._password:
            return {"success": False, "message": "请先在插件配置中填写馒头用户名与密码"}
        if self._run_lock.locked():
            return {"success": False, "message": "已有一次登录正在执行，请稍后再试"}

        def _job() -> None:
            """删除持久化浏览器配置目录后重新登录，强制重置设备受信 30 天。"""
            profile = self._profile_dir()
            if profile.exists():
                try:
                    shutil.rmtree(profile, ignore_errors=True)
                    logger.info("馒头自动登录：已清空浏览器设备身份，准备重新验证")
                except Exception as err:  # noqa: BLE001 - 删除失败仍尝试登录
                    logger.warning(f"馒头自动登录：清空设备身份失败：{err}")
            self.run_login()

        self._start_thread(_job)
        return {"success": True, "message": "已开始重新验证，稍后按提示填写邮箱验证码"}

    # ------------------------------------------------------------------
    # 配置与结果
    # ------------------------------------------------------------------

    def _current_config(self) -> Dict[str, Any]:
        """组装当前配置字典，用于回写与表单默认值。

        :return: 完整配置字典。
        """
        return {
            "enabled": self._enabled,
            "cron": self._cron,
            "login_url": self._login_url,
            "home_url": self._home_url,
            "username": self._username,
            "password": self._password,
            "email": self._email,
            "totp_secret": self._totp_secret,
            "notify_success": self._notify_success,
            "use_proxy": self._use_proxy,
            "code_wait": self._code_wait,
            "retry_interval": self._retry_interval,
            "retry_times": self._retry_times,
            "onlyonce": self._onlyonce,
            "last_result": self._last_result,
        }

    @staticmethod
    def _public_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """把内部结果裁剪为可安全下发前端的字段。

        :param result: 内部保存的结果字典。
        :return: 脱敏后的结果，空结果返回 None。
        """
        if not result:
            return None
        return {
            "at": result.get("at"),
            "success": bool(result.get("success")),
            "message": result.get("message") or "",
            "seconds": result.get("seconds"),
            "mode": result.get("mode") or "",
            "verify": result.get("verify") or "",
            "last_browse": result.get("last_browse") or "",
            "remaining": result.get("remaining"),
            "screenshot": result.get("screenshot") or "",
        }

    def _save_result(self, result: Dict[str, Any]) -> None:
        """保存本次结果到配置与历史记录。

        :param result: 本次登录结果字典。
        """
        self._last_result = result
        self.update_config(self._current_config())
        history = self.get_data("login_history") or []
        history.insert(0, result)
        self.save_data("login_history", history[: self.HISTORY_LIMIT])

    def _next_run_text(self) -> str:
        """按 cron 表达式推算下一次自动登录时间。

        :return: 下次执行时间文本，无法推算时返回空串。
        """
        if not self._enabled:
            return ""
        try:
            tz = pytz.timezone(str(get_runtime_setting("TZ") or "Asia/Shanghai"))
            now = datetime.now(tz=tz)
            trigger = CronTrigger.from_crontab(self._cron, timezone=tz)
            moment = trigger.get_next_fire_time(None, now)
            return moment.strftime("%Y-%m-%d %H:%M") if moment else ""
        except Exception:  # noqa: BLE001 - 仅用于展示
            return ""

    # ------------------------------------------------------------------
    # 登录主流程
    # ------------------------------------------------------------------

    def run_login(self) -> Dict[str, Any]:
        """执行一次浏览器登录保活，并按结果推送通知。

        :return: 本次登录结果字典。
        """
        if not self._run_lock.acquire(blocking=False):
            logger.info("馒头自动登录：已有登录任务在执行，本次跳过")
            return {}
        started = time.time()
        result: Dict[str, Any] = {
            "at": self._now_text(),
            "success": False,
            "message": "",
            "seconds": 0,
            "mode": "",
            "verify": "",
        }
        context = None
        try:
            if not self._username or not self._password:
                result["message"] = "未配置用户名或密码，跳过登录"
                logger.warning("馒头自动登录：%s", result["message"])
            else:
                context = self._open_context()
                page = context.new_page()
                page.set_default_timeout(30000)
                outcome = self._visit_and_login(page)
                result.update(outcome)
                if result.get("success"):
                    verify = self._verify_by_api()
                    result["verify"] = verify.get("message", "")
                    result["last_browse"] = verify.get("last_browse", "")
                    result["remaining"] = verify.get("remaining")
                    logger.info("馒头自动登录：%s，%s", result.get("message"),
                                result["verify"] or "未做接口复核")
                else:
                    logger.warning("馒头自动登录：失败，%s", result.get("message"))
        except Exception as err:  # noqa: BLE001 - 任何异常都要落结果并通知
            logger.error(f"馒头自动登录执行异常：{err}")
            result["success"] = False
            result["message"] = f"执行异常：{str(err)[:300]}"
        finally:
            self._awaiting_code = False
            self._code_event.clear()
            self._pending_code = ""
            if context is not None:
                try:
                    context.close()
                except Exception as err:  # noqa: BLE001 - 关闭失败不影响结果
                    logger.debug(f"馒头自动登录：关闭浏览器失败：{err}")
            result["seconds"] = round(time.time() - started, 1)
            self._run_lock.release()

        self._save_result(result)
        self._notify(result)
        if result.get("success"):
            self._maybe_device_reminder()
        elif result.get("mode") == "code":
            self._schedule_retry()
        return result

    def _visit_and_login(self, page: Any) -> Dict[str, Any]:
        """先尝试直接存取首页，必要时再走登录流程。

        :param page: 浏览器页面对象。
        :return: 登录结果字典。
        """
        page.goto(self._home_url, wait_until="domcontentloaded")
        self._wait_rendered(page)
        if self._session_ok(page):
            return {"success": True, "mode": "visit", "message": "设备仍受信，已存取首页完成保活"}

        logger.info("馒头自动登录：需要登录，打开 %s", self._login_url)
        page.goto(self._login_url, wait_until="domcontentloaded")
        self._settle(page, 2)
        if not self._fill_login_form(page):
            return {
                "success": False,
                "mode": "form",
                "message": f"未找到登录输入框（当前地址 {page.url}）"
                + self._shot_suffix(page),
            }
        self._submit_login(page)
        return self._handle_after_submit(page)

    def _handle_after_submit(self, page: Any) -> Dict[str, Any]:
        """提交账号密码后，处理验证码页与最终结果。

        :param page: 浏览器页面对象。
        :return: 登录结果字典。
        """
        deadline = time.time() + self.LOGIN_TIMEOUT
        last_text = ""
        while time.time() < deadline:
            self._settle(page, 1)
            last_text = self._page_text(page)
            if self._session_ok(page):
                return {"success": True, "mode": "login", "message": "账号密码登录成功"}

            error = self._match_error(last_text)
            if error:
                return {
                    "success": False,
                    "mode": "form",
                    "message": f"登录被拒绝：{error}" + self._shot_suffix(page),
                }

            if self._is_code_page(page, last_text):
                return self._handle_code_page(page, last_text)

            if self._needs_totp(last_text):
                if not self._totp_secret:
                    return {
                        "success": False,
                        "mode": "totp",
                        "message": "账号要求二级验证，但插件未配置 TOTP 密钥"
                        + self._shot_suffix(page),
                    }
                if self._submit_totp(page):
                    break
            time.sleep(1.5)

        # 提交二级验证码后继续观察最终结果
        deadline = time.time() + self.LOGIN_TIMEOUT
        while time.time() < deadline:
            self._settle(page, 1)
            last_text = self._page_text(page)
            if self._session_ok(page):
                return {"success": True, "mode": "totp", "message": "二级验证通过，登录成功"}
            error = self._match_error(last_text)
            if error:
                return {
                    "success": False,
                    "mode": "totp",
                    "message": f"二级验证被拒绝：{error}" + self._shot_suffix(page),
                }
            time.sleep(1.5)
        brief = last_text.replace("\n", " ")[:120]
        return {
            "success": False,
            "mode": "timeout",
            "message": f"登录超时（{self.LOGIN_TIMEOUT} 秒）：{brief}" + self._shot_suffix(page),
        }

    def _handle_code_page(self, page: Any, text: str) -> Dict[str, Any]:
        """处理邮箱验证码页：自动发码、通知使用者、等待手动填入。

        :param page: 浏览器页面对象。
        :param text: 当前页面文本。
        :return: 登录结果字典。
        """
        # 配置了 TOTP 密钥时先尝试验证器码，成功则完全无需人工介入
        if self._totp_secret and self._try_totp_on_verify_page(page, text):
            self._mark_device_verified()
            return {"success": True, "mode": "totp",
                    "message": "验证器动态码验证通过，登录成功（无需人工补码）"}

        # 页面要求填邮箱时补上配置的邮箱
        if self._mark(page, "input", ("郵箱", "邮箱", "email")):
            try:
                current = str(page.input_value(self._PICK) or "").strip()
            except Exception:  # noqa: BLE001 - 读取失败按空处理
                current = ""
            if not current and self._email:
                page.fill(self._PICK, self._email)

        sent = False
        if self._mark(page, "button", ("獲取驗證碼", "获取验证码", "獲取驗證", "發送驗證碼", "发送验证码")):
            traffic: List[Dict[str, Any]] = []

            def _on_response(resp: Any) -> None:
                """记录验证码请求相关的网络响应，便于判断是否真的发出。"""
                try:
                    url = str(resp.url or "")
                    if not any(k in url.lower() for k in ("auth", "email", "mail", "captcha", "code", "otp")):
                        return
                    item: Dict[str, Any] = {"url": url.split("?")[0], "status": resp.status}
                    try:
                        body = resp.text()
                        item["body"] = body[:300].replace("\n", " ")
                    except Exception:  # noqa: BLE001 - 非文本响应
                        pass
                    traffic.append(item)
                except Exception:  # noqa: BLE001 - 监听器不得抛异常
                    pass

            try:
                page.on("response", _on_response)
            except Exception as err:  # noqa: BLE001 - 监听失败不影响点击
                logger.debug(f"馒头自动登录：挂载网络监听失败：{err}")
            try:
                page.click(self._PICK)
                sent = True
                logger.info("馒头自动登录：已点击获取验证码")
            except Exception as err:  # noqa: BLE001 - 点击失败沿用已收到的码
                logger.warning(f"馒头自动登录：点击获取验证码失败：{err}")
            time.sleep(6)
            for item in traffic:
                logger.info("馒头自动登录：验证码请求 %s -> %s %s",
                            item.get("url"), item.get("status"), item.get("body") or "")
            toast = self._feedback_text(page)
            if toast:
                logger.info("馒头自动登录：页面提示 %s", toast)

        shot = self._save_screenshot(page)
        self._awaiting_code = True
        self._pending_code = ""
        self._code_event.clear()
        self._code_requested_at = self._now_text()
        self._code_deadline = self._deadline_text(self._code_wait)
        self._notify_code_needed(sent, shot)

        if self._wait_and_submit_code(page, text):
            return {"success": True, "mode": "code", "message": "邮箱验证码验证通过，登录成功"}
        return {
            "success": False,
            "mode": "code",
            "message": (
                f"设备验证到期，已自动发送邮箱验证码，但 {self._code_wait} 秒内未收到手动填入的验证码"
            ) + self._shot_suffix(page),
        }

    def _try_totp_on_verify_page(self, page: Any, text: str) -> bool:
        """在站点验证页直接提交 TOTP 动态码。

        站点验证页的输入框同时接受邮箱验证码与验证器动态码，账号开启 OTP
        二级验证后填入动态码即可完成验证，无需读取邮箱或人工介入。

        :param page: 浏览器页面对象。
        :param text: 当前页面文本。
        :return: 是否验证成功。
        """
        for attempt in range(2):
            code = self._totp_code(self._totp_secret)
            if not code:
                return False
            if not self._mark(page, "input", ("6位", "6 位", "驗證碼", "验证码", "code", "otp")):
                return False
            try:
                page.fill(self._PICK, code)
                logger.info("馒头自动登录：已填入验证器动态码（第 %s 次）", attempt + 1)
            except Exception as err:  # noqa: BLE001 - 填写失败退回人工补码
                logger.warning(f"馒头自动登录：填入验证器动态码失败：{err}")
                return False
            if not self._submit_login(page):
                return False
            confirm_deadline = time.time() + 30
            while time.time() < confirm_deadline:
                self._settle(page, 1)
                current_text = self._page_text(page)
                if self._session_ok(page):
                    logger.info("馒头自动登录：验证器动态码验证通过")
                    return True
                if "驗證碼錯誤" in current_text or "验证码错误" in current_text:
                    logger.warning("馒头自动登录：验证器动态码被拒绝，等待下一周期重试")
                    break
                if not self._is_code_page(page, current_text):
                    return self._session_ok(page)
            time.sleep(max(31 - int(time.time()) % 30, 1))
        return False

    def _wait_and_submit_code(self, page: Any, text: str) -> bool:
        """等待使用者提交验证码并完成登录。

        :param page: 浏览器页面对象。
        :param text: 进入验证码页时的页面文本。
        :return: 是否验证成功。
        """
        deadline = time.time() + self._code_wait
        while time.time() < deadline:
            if self._take_code_file():
                self._code_event.set()
            if self._code_event.wait(timeout=2):
                self._code_event.clear()
                code = self._pending_code.strip()
                self._pending_code = ""
                if not code:
                    continue
                logger.info("馒头自动登录：收到手动填入的验证码，正在提交")
                if not self._submit_code(page, code):
                    continue
                confirm_deadline = time.time() + 40
                while time.time() < confirm_deadline:
                    self._settle(page, 1)
                    current_text = self._page_text(page)
                    if self._session_ok(page):
                        self._mark_device_verified()
                        return True
                    if "驗證碼錯誤" in current_text or "验证码错误" in current_text:
                        logger.warning("馒头自动登录：验证码被判定错误，可重新提交")
                        break
                    error = self._match_error(current_text)
                    if error and "驗證碼" not in error:
                        logger.warning("馒头自动登录：验证码提交后被拒绝：%s", error)
                        break
            elif not self._session_ok(page):
                # 期间页面可能已自行完成登录
                if not self._is_code_page(page, text):
                    return True
        return False

    def _take_code_file(self) -> bool:
        """读取外部投递的验证码文件，用于不方便打开插件页面时补码。

        外部只需把验证码写入插件数据目录下的 ``code.txt``，本方法读取后立即删除，
        避免过期验证码被下一轮误用。

        :return: 是否取到了新验证码。
        """
        if self._pending_code:
            return False
        path = self.get_data_path() / "code.txt"
        if not path.exists():
            return False
        try:
            code = path.read_text(encoding="utf-8").strip().replace(" ", "")
        except Exception as err:  # noqa: BLE001 - 读取失败按未投递处理
            logger.warning(f"馒头自动登录：读取投递验证码失败：{err}")
            return False
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001 - 删除失败不影响本次使用
                pass
        if not code:
            return False
        self._pending_code = code
        logger.info("馒头自动登录：检测到外部投递的验证码")
        return True

    def _submit_code(self, page: Any, code: str) -> bool:
        """把验证码填入页面并提交。

        :param page: 浏览器页面对象。
        :param code: 6 位邮箱验证码。
        :return: 是否成功提交。
        """
        try:
            if not self._mark(page, "input", ("6位", "6 位", "驗證碼", "验证码", "code")):
                logger.warning("馒头自动登录：未找到验证码输入框")
                return False
            page.fill(self._PICK, code)
            self._submit_login(page)
            return True
        except Exception as err:  # noqa: BLE001 - 提交失败由调用方记录
            logger.warning(f"馒头自动登录：提交验证码失败：{err}")
            return False

    # ------------------------------------------------------------------
    # 浏览器与页面操作
    # ------------------------------------------------------------------

    def _open_context(self) -> Any:
        """启动持久化浏览器上下文，保持站点设备受信身份。

        :return: Playwright 浏览器上下文。
        """
        try:
            import cloakbrowser
        except Exception as err:  # noqa: BLE001 - 缺少浏览器依赖时明确报错
            raise RuntimeError(f"浏览器依赖不可用：{err}") from err
        # 宿主的浏览器名额包装只覆盖其公开入口；持久化启动需先登记包装，
        # 否则会绕过实例名额控制，这里显式初始化一次（失败不影响启动）。
        try:
            from app.adapters.network.browser import configure_browser_queue

            configure_browser_queue()
        except Exception as err:  # noqa: BLE001 - 包装缺失仅影响并发限额
            logger.debug(f"馒头自动登录：初始化浏览器名额包装失败：{err}")
        profile = self._profile_dir()
        profile.mkdir(parents=True, exist_ok=True)
        return cloakbrowser.launch_persistent_context(
            user_data_dir=str(profile),
            headless=True,
            locale="zh-TW",
            timezone=str(get_runtime_setting("TZ") or "Asia/Shanghai"),
            proxy=self._proxy_url(),
        )

    def _profile_dir(self) -> Any:
        """返回持久化浏览器配置目录。

        :return: 配置目录路径对象。
        """
        return self.get_data_path() / "profile"

    @staticmethod
    def _wait_rendered(page: Any, timeout: float = 30.0) -> None:
        """等待单页应用完成首屏渲染。

        :param page: 浏览器页面对象。
        :param timeout: 等待上限秒数。
        """
        deadline = time.time() + max(timeout, 1)
        while time.time() < deadline:
            try:
                if (page.inner_text("body") or "").strip():
                    return
            except Exception:  # noqa: BLE001 - 渲染过程中读取可能失败
                pass
            time.sleep(1.0)

    @staticmethod
    def _settle(page: Any, seconds: float) -> None:
        """等待页面渲染稳定，忽略等待期间的异常。

        :param page: 浏览器页面对象。
        :param seconds: 等待秒数。
        """
        try:
            page.wait_for_load_state("domcontentloaded", timeout=int(seconds * 1000))
        except Exception:  # noqa: BLE001 - 加载状态超时不阻塞流程
            pass
        time.sleep(seconds)

    def _session_ok(self, page: Any) -> bool:
        """判断当前页面是否已处于登录态。

        :param page: 浏览器页面对象。
        :return: 已登录返回 True。
        """
        try:
            url = str(page.url or "")
            path = urlparse(url).path or ""
            if "login" in path.lower():
                return False
            if page.query_selector("#password") is not None:
                return False
            body = self._page_text(page)
            if not body.strip():
                return False
            # 登录页特征文案仍在，且出现用户名/密码字样，判定为未登录
            for keyword in ("Sign in to MTeam", "登 錄 MTeam", "登錄 MTeam"):
                if keyword in body and ("用戶名" in body or "密碼" in body):
                    return False
            return True
        except Exception:  # noqa: BLE001 - 页面切换期间按未登录处理
            return False

    def _fill_login_form(self, page: Any) -> bool:
        """填写用户名与密码。

        :param page: 浏览器页面对象。
        :return: 是否成功填写。
        """
        if not self._mark(page, "input", ("用戶名", "用户名", "username")):
            return False
        try:
            page.fill(self._PICK, self._username)
        except Exception as err:  # noqa: BLE001 - 填写失败视为表单不可用
            logger.warning(f"馒头自动登录：填写用户名失败：{err}")
            return False
        if not self._mark(page, "input", ("密碼", "密码", "password")):
            return False
        try:
            page.fill(self._PICK, self._password)
        except Exception as err:  # noqa: BLE001 - 填写失败视为表单不可用
            logger.warning(f"馒头自动登录：填写密码失败：{err}")
            return False
        return True

    def _submit_login(self, page: Any) -> bool:
        """点击登录按钮。

        :param page: 浏览器页面对象。
        :return: 是否点击成功。
        """
        for needle in ("登 錄", "登錄", "登入", "登 入", "提交"):
            if self._mark(page, "button", (needle,)):
                try:
                    page.click(self._PICK)
                    return True
                except Exception as err:  # noqa: BLE001 - 尝试下一个候选
                    logger.debug(f"馒头自动登录：点击登录按钮失败：{err}")
        try:
            button = page.query_selector("button[type=submit]")
            if button:
                button.click()
                return True
        except Exception as err:  # noqa: BLE001 - 兜底失败
            logger.warning(f"馒头自动登录：未找到登录按钮：{err}")
        return False

    def _is_code_page(self, page: Any, text: str) -> bool:
        """判断当前是否为邮箱验证码页。

        :param page: 浏览器页面对象。
        :param text: 页面文本。
        :return: 是验证码页返回 True。
        """
        for keyword in ("郵箱驗證碼", "邮箱验证码", "6位數字驗證碼", "6位数字验证码"):
            if keyword in text:
                return True
        try:
            if page.query_selector("#password") is not None:
                return False
        except Exception:  # noqa: BLE001 - 查询失败按文本判断
            pass
        return any(word in text for word in ("獲取驗證碼", "获取验证码"))

    @classmethod
    def _mark(cls, page: Any, kind: str, needles: Tuple[str, ...],
              timeout: float = 25.0) -> bool:
        """在页面中轮询定位元素并打上可复用标记。

        站点前端是单页应用，首屏渲染在低配环境下可能耗时 20 秒以上，
        因此按超时轮询，不能在 DOM 刚就绪时只查一次。

        :param page: 浏览器页面对象。
        :param kind: 元素类型，input 或 button。
        :param needles: 依次尝试的关键字。
        :param timeout: 轮询上限秒数。
        :return: 是否定位到元素。
        """
        script = """
        (args) => {
          const [kind, needles] = args;
          const ATTR = 'data-mp-pick';
          document.querySelectorAll('[' + ATTR + ']').forEach((e) => e.removeAttribute(ATTR));
          const selector = kind === 'input' ? 'input, textarea' : 'button, [role="button"], a';
          const nodes = Array.from(document.querySelectorAll(selector));
          const norm = (value) => (value || '').replace(/\\s+/g, '');
          for (const needle of needles) {
            const target = norm(needle);
            if (!target) continue;
            for (const el of nodes) {
              const rect = el.getBoundingClientRect();
              if (rect.width <= 0 || rect.height <= 0) continue;
              const text = norm(el.innerText || el.textContent || '');
              const hint = norm([
                el.getAttribute('placeholder') || '',
                el.getAttribute('name') || '',
                el.getAttribute('id') || '',
                el.getAttribute('type') || '',
                el.getAttribute('aria-label') || '',
              ].join(' '));
              const hay = kind === 'input' ? hint + text : text + hint;
              if (hay.indexOf(target) >= 0) {
                el.setAttribute(ATTR, '1');
                return true;
              }
            }
          }
          return false;
        }
        """
        deadline = time.time() + max(timeout, 1)
        while time.time() < deadline:
            try:
                if page.evaluate(script, [kind, list(needles)]):
                    return True
            except Exception as err:  # noqa: BLE001 - 渲染过程中查询可能失败
                logger.debug(f"馒头自动登录：定位元素失败：{err}")
            time.sleep(0.8)
        return False

    # ------------------------------------------------------------------
    # 页面文本与截图
    # ------------------------------------------------------------------

    @staticmethod
    def _feedback_text(page: Any) -> str:
        """提取页面浮层提示（toast、提示框）文本，用于判断操作是否被接受。

        :param page: 当前浏览器页面对象。
        :return: 提示文本，未取到返回空串。
        """
        script = """
        () => {
          const nodes = Array.from(document.querySelectorAll(
            '[role="alert"], .toast, .Toastify, .v-snackbar, .notyf, .swal2-popup, .el-message, .ant-message'
          ));
          const texts = nodes.map((el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim())
            .filter((t) => t);
          return texts.slice(0, 3).join(' | ').slice(0, 300);
        }
        """
        try:
            return str(page.evaluate(script) or "").strip()
        except Exception:  # noqa: BLE001 - 取提示失败不影响流程
            return ""

    @staticmethod
    def _page_text(page: Any) -> str:
        """读取当前页面正文文本。

        :param page: 当前浏览器页面对象。
        :return: 页面文本，读取失败时返回空串。
        """
        try:
            return str(page.inner_text("body") or "")
        except Exception:  # noqa: BLE001 - 页面跳转期间可能取不到
            return ""

    def _shot_suffix(self, page: Any) -> str:
        """保存现场截图并返回可拼接的提示后缀。

        :param page: 当前浏览器页面对象。
        :return: 形如「（截图：last_failure.png）」的后缀，失败返回空串。
        """
        shot = self._save_screenshot(page)
        return f"（截图：{shot}）" if shot else ""

    def _save_screenshot(self, context: Any) -> str:
        """把当前页面截图写入插件数据目录，便于排查。

        :param context: 浏览器上下文或页面对象。
        :return: 截图文件名，保存失败返回空串。
        """
        if context is None:
            return ""
        try:
            path = self.get_data_path() / "last_failure.png"
            page = context
            if hasattr(context, "pages"):
                pages = list(getattr(context, "pages", []) or [])
                if not pages:
                    return ""
                page = pages[-1]
            page.screenshot(path=str(path), full_page=True)
            return "last_failure.png"
        except Exception as err:  # noqa: BLE001 - 截图仅用于辅助
            logger.debug(f"馒头自动登录：保存截图失败：{err}")
            return ""

    @staticmethod
    def _match_error(text: str) -> str:
        """从页面文本中识别常见登录失败提示。

        :param text: 页面正文文本。
        :return: 命中的错误说明，未命中返回空串。
        """
        for keyword in ("密碼錯誤", "密码错误", "用戶名或用戶密碼不正確", "用户名或密码不正确",
                        "帳號或密碼錯誤", "账号或密码错误", "登入失敗", "登录失败",
                        "帳號已被禁用", "账号已被禁用", "驗證碼錯誤", "验证码错误"):
            if keyword in text:
                return keyword
        return ""

    @staticmethod
    def _needs_totp(text: str) -> bool:
        """判断页面是否要求二次验证码（非邮箱验证码）。

        :param text: 页面正文文本。
        :return: 是否需要二次验证。
        """
        if "郵箱" in text or "邮箱" in text:
            return False
        for keyword in ("二級驗證", "二级验证", "兩步驟", "两步", "動態驗證碼", "动态验证码",
                        "Google Authenticator"):
            if keyword in text:
                return True
        return False

    def _submit_totp(self, page: Any) -> bool:
        """计算并提交 TOTP 验证码。

        :param page: 当前浏览器页面对象。
        :return: 是否成功提交。
        """
        try:
            code = self._totp_code(self._totp_secret)
            if not code:
                return False
            if not self._mark(page, "input", ("動態", "动态", "驗證碼", "验证码", "otp", "code")):
                return False
            page.fill(self._PICK, code)
            return self._submit_login(page)
        except Exception as err:  # noqa: BLE001 - 二次验证失败仅记录
            logger.warning(f"馒头自动登录：提交二次验证码失败：{err}")
            return False

    @staticmethod
    def _totp_code(secret: str) -> str:
        """按 RFC 6238 计算 30 秒周期的 6 位 TOTP 验证码。

        :param secret: Base32 编码的 TOTP 密钥。
        :return: 6 位验证码，密钥非法时返回空串。
        """
        raw = (secret or "").strip().upper().replace(" ", "")
        if not raw:
            return ""
        padding = "=" * ((8 - len(raw) % 8) % 8)
        try:
            key = b32decode(raw + padding)
        except Exception:  # noqa: BLE001 - 密钥格式错误
            return ""
        counter = int(time.time()) // 30
        digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        return f"{code % 1000000:06d}"

    # ------------------------------------------------------------------
    # 设备受信与重试
    # ------------------------------------------------------------------

    def _mark_device_verified(self) -> None:
        """记录本次设备验证成功日期，用于 30 天到期提醒。"""
        self.save_data("device_verified_at", self._today_text())
        logger.info("馒头自动登录：设备验证成功，受信期重置为 %s 天", self.DEVICE_VALID_DAYS)

    def _device_days_since(self) -> Optional[int]:
        """计算距上次设备验证成功已过多少天。

        :return: 天数，无记录时返回 None。
        """
        raw = str(self.get_data("device_verified_at") or "").strip()
        if not raw:
            return None
        try:
            verified = datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
        return max((datetime.strptime(self._today_text(), "%Y-%m-%d") - verified).days, 0)

    def _maybe_device_reminder(self) -> None:
        """设备受信接近 30 天时提醒提前补码，每天最多提醒一次。"""
        days = self._device_days_since()
        if days is None or days < self.DEVICE_WARN_DAYS:
            return
        today = self._today_text()
        if str(self.get_data("last_device_reminder") or "") == today:
            return
        self.save_data("last_device_reminder", today)
        expire_in = max(self.DEVICE_VALID_DAYS - days, 0)
        try:
            self.post_message(
                title="【馒头】设备验证即将到期，请补一次验证码",
                text=(
                    f"当前设备验证已过 {days} 天，站点受信期 {self.DEVICE_VALID_DAYS} 天，"
                    f"预计还剩 {expire_in} 天。\n"
                    "请在方便时打开插件页面，点「立即登录」，插件会自动发送邮箱验证码，"
                    "填入后受信期重新计算 30 天。\n"
                    "这样可避免恰好在不方便的时间点被动补码。"
                ),
            )
        except Exception as err:  # noqa: BLE001 - 提醒失败不影响主流程
            logger.warning(f"馒头自动登录：到期提醒推送失败：{err}")

    def _schedule_retry(self) -> None:
        """验证码未填入时按配置安排重试，避免整日无人值守空转。"""
        if self._retry_times <= 0:
            return
        state = self.get_data("retry_state") or {}
        today = self._today_text()
        count = int(state.get("count") or 0) if str(state.get("date") or "") == today else 0
        if count >= self._retry_times:
            logger.info("馒头自动登录：今日补码重试已达上限 %s 次", self._retry_times)
            return
        self.save_data("retry_state", {"date": today, "count": count + 1})
        delay = max(self._retry_interval, 1) * 60
        logger.info("馒头自动登录：%s 分钟后重试第 %s 次", self._retry_interval, count + 1)
        timer = threading.Timer(delay, self.run_login)
        timer.daemon = True
        timer.start()

    def _start_thread(self, func: Any) -> None:
        """以后台守护线程执行任务。

        :param func: 目标可调用对象。
        """
        thread = threading.Thread(target=func, name="MTeamAutoLogin", daemon=True)
        thread.start()

    def _proxy_url(self) -> Optional[str]:
        """按配置决定浏览器是否走系统代理，默认与站点一致直连。

        :return: 代理地址，直连或未配置时返回 None。
        """
        if not self._use_proxy:
            return None
        proxy = get_runtime_setting("PROXY")
        if not proxy:
            return None
        if isinstance(proxy, str):
            return proxy or None
        if isinstance(proxy, dict):
            return proxy.get("https") or proxy.get("http") or None
        return None

    # ------------------------------------------------------------------
    # 站点复核
    # ------------------------------------------------------------------

    def _verify_by_api(self) -> Dict[str, Any]:
        """用站点 ApiKey 读取资料接口，复核最近浏览时间是否已更新。

        :return: 含说明、最近浏览时间与剩余天数的字典。
        """
        site = self._get_site()
        if not site or not getattr(site, "apikey", None):
            return {"message": "站点未配置 ApiKey，未能复核"}
        host = self._api_host(site)
        if not host:
            return {"message": "未能解析站点 API 域名，未能复核"}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "x-api-key": site.apikey,
            "User-Agent": getattr(site, "ua", None) or "Mozilla/5.0",
        }
        try:
            res = RequestUtils(
                headers=headers,
                proxies=get_runtime_setting("PROXY") if getattr(site, "proxy", 0) else None,
                timeout=30,
            ).post_res(f"https://{host}/api/member/profile", json={})
            if not res or res.status_code != 200:
                return {"message": f"资料接口返回 {getattr(res, 'status_code', '未知')}，未能复核"}
            payload = res.json()
        except Exception as err:  # noqa: BLE001 - 复核失败不影响登录结果
            return {"message": f"资料接口请求异常：{str(err)[:120]}"}
        if str(payload.get("code")) != "0":
            return {"message": f"资料接口返回异常：{payload.get('message') or payload.get('code')}"}
        data = payload.get("data") or {}
        member_status = data.get("memberStatus") or {}
        browse = str(member_status.get("lastBrowse") or "").strip()
        if not browse:
            return {"message": "资料接口未返回最近浏览时间"}
        try:
            browse_at = datetime.strptime(browse[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {"message": f"最近浏览时间格式异常：{browse}", "last_browse": browse}
        tz = pytz.timezone(str(get_runtime_setting("TZ") or "Asia/Shanghai"))
        days_since = max((datetime.now(tz=tz).date() - browse_at.date()).days, 0)
        remaining = self.KEEPALIVE_DAYS - days_since
        if days_since == 0:
            message = f"站点已记录今天浏览（{browse}），保活生效"
        else:
            message = f"站点记录的最近浏览仍是 {browse}（{days_since} 天前），可能未计入保活"
        return {"message": message, "last_browse": browse, "remaining": remaining}

    def _get_site(self):
        """定位馒头站点记录。

        :return: 站点对象，未找到返回 None。
        """
        try:
            for site in SiteOper().list_order_by_pri():
                domain = str(getattr(site, "domain", "") or getattr(site, "url", "") or "").lower()
                if "m-team" in domain:
                    return site
        except Exception as err:  # noqa: BLE001 - 站点查询失败仅影响复核
            logger.warning(f"馒头自动登录：读取站点信息失败：{err}")
        return None

    @staticmethod
    def _api_host(site: Any) -> str:
        """从站点配置解析 API 主机名。

        :param site: 站点记录对象。
        :return: 形如 api.m-team.io 的主机名，解析失败返回空串。
        """
        hosts: List[str] = []
        for value in (getattr(site, "url", ""), getattr(site, "domain", "")):
            raw = str(value or "").strip()
            if not raw:
                continue
            parsed = urlparse(raw if "://" in raw else f"//{raw}")
            host = (parsed.netloc or parsed.path.split("/", 1)[0]).split("@")[-1]
            if host and host not in hosts:
                hosts.append(host)
        # 优先使用站点里已经带 api. 前缀的主机
        for host in hosts:
            if host.startswith("api."):
                return host
        for host in hosts:
            parts = host.split(".")
            if len(parts) == 2:
                # 形如 m-team.io 的注册域名，接口主机是 api.m-team.io
                return f"api.{host}"
            if len(parts) > 2:
                # 形如 kp.m-team.cc，去掉最左侧的子域再补 api.
                return f"api.{'.'.join(parts[1:])}"
        return ""

    # ------------------------------------------------------------------
    # 时间与通知
    # ------------------------------------------------------------------

    def _today_text(self) -> str:
        """返回当前时区的日期文本。

        :return: 形如 2026-11-14 的日期。
        """
        try:
            tz = pytz.timezone(str(get_runtime_setting("TZ") or "Asia/Shanghai"))
        except Exception:  # noqa: BLE001 - 时区异常时退回本地时间
            return datetime.now().strftime("%Y-%m-%d")
        return datetime.now(tz=tz).strftime("%Y-%m-%d")

    @staticmethod
    def _now_text() -> str:
        """返回当前时区的可读时间。

        :return: 形如 2026-11-14 08:17:00 的时间文本。
        """
        try:
            tz = pytz.timezone(str(get_runtime_setting("TZ") or "Asia/Shanghai"))
        except Exception:  # noqa: BLE001 - 时区异常时退回本地时间
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")

    def _deadline_text(self, seconds: int) -> str:
        """按等待秒数推算截止时间。

        :param seconds: 等待秒数。
        :return: 形如 08:27:00 的截止时间文本。
        """
        try:
            tz = pytz.timezone(str(get_runtime_setting("TZ") or "Asia/Shanghai"))
            moment = datetime.now(tz=tz) + timedelta(seconds=seconds)
            return moment.strftime("%H:%M:%S")
        except Exception:  # noqa: BLE001 - 仅用于展示
            return ""

    def _notify_code_needed(self, sent: bool, shot: str) -> None:
        """通知使用者需要手动填写邮箱验证码。

        :param sent: 是否已成功点击发送验证码。
        :param shot: 现场截图文件名。
        """
        lines = [
            f"时间：{self._code_requested_at}",
            "站点设备验证已到期，本次登录需要邮箱验证码。",
            "已自动点击「获取验证码」" if sent else "未能自动点击发送，请在页面点「获取验证码」",
            f"请在本通知页打开插件，于 {self._code_deadline} 前填入邮箱收到的验证码。",
            f"若当时不方便：忽略即可，插件会在 {self._retry_interval} 分钟后自动重试并发新码，"
            f"每日最多 {self._retry_times} 次；也可随时在插件页点「立即登录」重新发码。",
            "也可以把验证码直接发给助手，由助手投递给插件提交。",
        ]
        if shot:
            lines.append(f"现场截图：{shot}")
        try:
            self.post_message(title="【馒头】需要填写邮箱验证码", text="\n".join(lines))
        except Exception as err:  # noqa: BLE001 - 通知失败不影响主流程
            logger.warning(f"馒头自动登录：验证码通知推送失败：{err}")

    def _notify(self, result: Dict[str, Any]) -> None:
        """按结果推送通知，成功默认静默、失败必发。

        :param result: 本次登录结果字典。
        """
        success = bool(result.get("success"))
        if success and not self._notify_success:
            return
        if success:
            title = "【馒头】自动登录成功"
        else:
            title = "【馒头】自动登录失败"
        lines = [
            f"执行时间：{result.get('at') or '-'}",
            f"结果：{result.get('message') or '-'}",
        ]
        if result.get("verify"):
            lines.append(f"站点复核：{result['verify']}")
        if result.get("remaining") is not None:
            lines.append(f"距 {self.KEEPALIVE_DAYS} 天保活线还剩：{result['remaining']} 天")
        if not success:
            lines.append("如提示需要邮箱验证码，请在插件页点「立即登录」并把邮件验证码填入。")
        try:
            self.post_message(title=title, text="\n".join(lines))
        except Exception as err:  # noqa: BLE001 - 通知失败不影响主流程
            logger.warning(f"馒头自动登录：消息推送失败：{err}")
