import asyncio
import functools
import inspect
from typing import Any, List, Dict, Tuple

from app.plugins import _PluginBase
from app.sdk.events import eventmanager, Event
from app.schemas.types import ChainEventType
from app.schemas import DiscoverSourceEventData

# 导入各探索源子模块
from .modules import tencentvideo, bilibili, cctv, mangguo, bangumidaily, migu
from .modules import iqiyi as iqiyi_module
from .modules import maoyan as maoyan_module

MODULE_LABELS = {
    "tencentvideo": "腾讯视频",
    "bilibili": "哔哩哔哩",
    "cctv": "CCTV",
    "mangguo": "芒果TV",
    "bangumidaily": "Bangumi每日放送",
    "migu": "咪咕视频",
}


class MediaExplore(_PluginBase):
    """
    媒体探索聚合插件。

    统一管理与注册多个国内视频站探索数据源，聚合为一个插件，
    避免依赖第三方探索聚合插件的更新与失效。每个源可在配置中独立开关。
    """

    # 插件名称
    plugin_name = "媒体探索聚合"
    # 插件描述
    plugin_desc = "聚合多个国内视频站探索数据源，统一开关与管理。"
    # 插件图标
    plugin_icon = "mediaexplore.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "local"
    # 作者主页
    author_url = None
    # 插件配置项ID前缀
    plugin_config_prefix = "mediaexplore_"
    # 加载顺序
    plugin_order = 12
    # 可使用的用户级别
    auth_level = 1

    # 子模块注册表
    modules = {
        "tencentvideo": tencentvideo,
        "bilibili": bilibili,
        "cctv": cctv,
        "mangguo": mangguo,
        "bangumidaily": bangumidaily,
        "migu": migu,
    }
    enabled_modules: Dict[str, bool] = {}

    def __init__(self):
        """初始化聚合插件及爱奇艺/猫眼源实例。"""
        super().__init__()
        self._iqiyi_source = iqiyi_module.IqiyiSource()
        self._maoyan_source = maoyan_module.MaoyanSource()

    def init_plugin(self, config: dict = None):
        """根据插件配置初始化各探索源的启用状态。"""
        if config:
            for name in self.modules:
                self.enabled_modules[name] = config.get(f"{name}_enabled", False)
            # 初始化爱奇艺源（启用状态、Cookie、定时刷新周期）
            self._iqiyi_source.init_plugin({
                "enabled": bool(config.get("iqiyi_enabled", False)),
                "cookie": config.get("iqiyi_cookie", ""),
                "refresh_cron": config.get("iqiyi_refresh_cron", ""),
            })
            # 初始化猫眼源
            self._maoyan_source.init_plugin({
                "enabled": bool(config.get("maoyan_enabled", False)),
            })
        else:
            for name in self.modules:
                self.enabled_modules[name] = False
            self._iqiyi_source.init_plugin({"enabled": False, "cookie": "", "refresh_cron": ""})
            self._maoyan_source.init_plugin({"enabled": False})

    def _iqiyi_enabled(self) -> bool:
        """返回爱奇艺源是否启用。"""
        return self._iqiyi_source.get_state()

    def _maoyan_enabled(self) -> bool:
        """返回猫眼源是否启用。"""
        return self._maoyan_source.get_state()

    def get_state(self) -> bool:
        """返回插件是否处于启用状态（任一源启用即视为启用）。"""
        return any(self.enabled_modules.values()) or self._iqiyi_enabled() or self._maoyan_enabled()

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回插件配置表单与默认配置。"""
        plugin_names = "、".join(MODULE_LABELS.values())
        form = [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VCard",
                        "props": {"class": "mt-0"},
                        "content": [
                            {
                                "component": "VCardTitle",
                                "props": {"class": "d-flex align-center"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {"style": "color: #16b1ff;", "class": "mr-2"},
                                        "text": "mdi-compass-outline"
                                    },
                                    {
                                        "component": "span",
                                        "text": "探索源开关"
                                    }
                                ]
                            },
                            {"component": "VDivider"},
                            {
                                "component": "VCardText",
                                "content": [
                                    {
                                        "component": "VRow",
                                        "content": [
                                            {
                                                "component": "VCol",
                                                "props": {"cols": 12, "md": 4},
                                                "content": [
                                                    {
                                                        "component": "VSwitch",
                                                        "props": {
                                                            "model": f"{name}_enabled",
                                                            "label": f"启用{MODULE_LABELS.get(name, name)}探索源",
                                                        },
                                                    }
                                                ],
                                            }
                                            for name in self.modules
                                        ]
                                        + [
                                            {
                                                "component": "VCol",
                                                "props": {"cols": 12, "md": 4},
                                                "content": [
                                                    {
                                                        "component": "VSwitch",
                                                        "props": {
                                                            "model": "iqiyi_enabled",
                                                            "label": "启用爱奇艺探索源",
                                                        },
                                                    }
                                                ],
                                            },
                                            {
                                                "component": "VCol",
                                                "props": {"cols": 12, "md": 4},
                                                "content": [
                                                    {
                                                        "component": "VSwitch",
                                                        "props": {
                                                            "model": "maoyan_enabled",
                                                            "label": "启用猫眼TOP30探索源",
                                                        },
                                                    }
                                                ],
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VCard",
                        "props": {"variant": "flat", "class": "mt-3", "color": "surface"},
                        "content": [
                            {
                                "component": "VCardTitle",
                                "props": {"class": "d-flex align-center text-h6"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {"style": "color: #16b1ff;", "class": "mr-2"},
                                        "text": "mdi-shield-key-outline"
                                    },
                                    {"component": "span", "text": "爱奇艺配置"}
                                ]
                            },
                            {"component": "VDivider"},
                            {
                                "component": "VCardText",
                                "props": {"class": "px-6"},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "iqiyi_cookie",
                                            "label": "爱奇艺 Cookie（可选）",
                                            "placeholder": "留空则由 CloakBrowser 自动获取；失效时可手动填入 Cookie",
                                            "hint": "爱奇艺接口有风控，插件会自动获取 Cookie（含 __dfp），失效后自动刷新。仅在自动获取失败时手动填入。"
                                        }
                                    },
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "iqiyi_refresh_cron",
                                            "label": "Cookie 定时刷新周期（Cron 表达式，可选）",
                                            "placeholder": "例如 0 */2 * * *（每 2 小时）",
                                            "hint": "留空则不启用定时刷新；建议每 2 小时刷新一次"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VCard",
                        "props": {"variant": "flat", "class": "mt-3", "color": "surface"},
                        "content": [
                            {
                                "component": "VCardText",
                                "props": {"class": "px-6"},
                                "content": [
                                    {
                                        "component": "div",
                                        "props": {"class": "text-body-1"},
                                        "text": "开启对应探索源后，将在 MoviePilot 探索页面展示对应数据源页面，可根据需要独立开启。"
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-body-1 mt-2"},
                                        "text": f"当前聚合源：{plugin_names}"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        default_data = {f"{name}_enabled": False for name in self.modules}
        default_data.update({
            "iqiyi_enabled": False,
            "iqiyi_cookie": "",
            "iqiyi_refresh_cron": "",
            "maoyan_enabled": False,
        })
        return form, default_data

    def get_api(self) -> List[Dict[str, Any]]:
        """返回各探索源的 API 端点列表，统一包装为前端要求的 envelope 结构。"""
        from app.schemas import MediaInfo, Response

        def _wrap_endpoint(endpoint):
            """把返回纯列表的探索端点包装为前端要求的 Response envelope，保留原签名。"""
            if not callable(endpoint):
                return endpoint
            if inspect.isasyncgenfunction(endpoint) or asyncio.iscoroutinefunction(endpoint):

                @functools.wraps(endpoint)
                async def _async_wrapped(*args, **kwargs):
                    data = await endpoint(*args, **kwargs)
                    if isinstance(data, dict) and "success" in data:
                        return data
                    return Response(success=True, data=data)

                _async_wrapped.__signature__ = inspect.signature(endpoint)
                return _async_wrapped

            @functools.wraps(endpoint)
            def _sync_wrapped(*args, **kwargs):
                data = endpoint(*args, **kwargs)
                if isinstance(data, dict) and "success" in data:
                    return data
                return Response(success=True, data=data)

            _sync_wrapped.__signature__ = inspect.signature(endpoint)
            return _sync_wrapped

        apis = []
        for name, mod in self.modules.items():
            if self.enabled_modules.get(name):
                for api in mod.get_api(self):
                    api = dict(api)
                    api["endpoint"] = _wrap_endpoint(api.get("endpoint"))
                    api["response_model"] = Response[List[MediaInfo]]
                    apis.append(api)
        # 爱奇艺端点本身已返回 Response envelope，无需再包装
        if self._iqiyi_enabled():
            for api in self._iqiyi_source.get_api():
                apis.append(dict(api))
        # 猫眼端点本身已返回 Response envelope，无需再包装
        if self._maoyan_enabled():
            for api in self._maoyan_source.get_api():
                apis.append(dict(api))
        return apis

    def get_page(self) -> List[dict]:
        """返回插件详情页面（本插件无需详情页）。"""
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """返回插件定时服务列表（爱奇艺 Cookie 定时刷新 + 猫眼缓存预热）。"""
        services = []
        if self._iqiyi_enabled():
            try:
                services.extend(self._iqiyi_source.get_service() or [])
            except Exception:
                pass
        if self._maoyan_enabled():
            try:
                services.extend(self._maoyan_source.get_service() or [])
            except Exception:
                pass
        return services

    def get_media_source(self) -> List[Dict[str, Any]]:
        """返回插件声明的媒体数据源（爱奇艺）。"""
        if self._iqiyi_enabled():
            try:
                return self._iqiyi_source.get_media_source() or []
            except Exception:
                pass
        return []

    @eventmanager.register(ChainEventType.DiscoverSource)
    def discover_source(self, event: Event):
        """监听探索源注册事件，注册所有已启用的探索数据源。"""
        event_data: DiscoverSourceEventData = event.event_data
        for name, mod in self.modules.items():
            if self.enabled_modules.get(name):
                mod.discover_source(self, event_data)
        # 注册爱奇艺探索源
        if self._iqiyi_enabled():
            self._iqiyi_source.discover_source(event)
        # 注册猫眼探索源
        if self._maoyan_enabled():
            self._maoyan_source.discover_source(event)

    def stop_service(self):
        """停止插件后台服务并释放资源。"""
        for name, mod in self.modules.items():
            if hasattr(mod, "stop_service"):
                mod.stop_service()
        try:
            self._iqiyi_source.stop_service()
        except Exception:
            pass
        try:
            self._maoyan_source.stop_service()
        except Exception:
            pass
