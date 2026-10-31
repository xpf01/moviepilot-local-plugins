"""来源抽象：运行期依赖上下文 + Provider 基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator, Optional

if TYPE_CHECKING:
    from .models import ProviderSpec, RankMediaItem


class ProviderContext:
    """运行期依赖注入容器（链、日志、退出信号、代理开关、插件 KV 读写）。"""

    def __init__(self, chain, downloadchain, subscribechain, logger, event=None, proxy: bool = False,
                 get_data=None, save_data=None, searchchain=None, systemconfig=None):
        self.chain = chain                    # 识别链（recognize_media）
        self.downloadchain = downloadchain    # 媒体库查重（get_no_exists_info）
        self.subscribechain = subscribechain  # 订阅查重/落地（exists / add）
        self.logger = logger
        self.event = event                    # threading.Event 退出信号
        self.proxy = proxy                    # 是否走系统代理
        # 插件 KV 读写（落 DB，供 provider 持久化缓存，如奈飞两级缓存的 L2）。
        # 可能为 None（测试 / 无 KV 时禁用持久化）；现有位置参数构造不受影响（新参在尾部、可选）。
        self.get_data = get_data              # 读插件 KV：get_data(key) -> value|None
        self.save_data = save_data            # 写插件 KV：save_data(key, value)
        # 搜索下载优先（可选）：searchchain 用于资源搜索，systemconfig 用于取订阅站点与过滤规则组。
        # 仅「豆瓣想看」这类需要「先搜资源直接下载、失败再回退订阅」的来源使用；其余来源为 None。
        self.searchchain = searchchain        # 资源搜索链（SearchChain.process）
        self.systemconfig = systemconfig      # 系统配置（SystemConfigOper，取 RssSites / 规则组）


class RankProvider(ABC):
    """榜单来源基类。子类以类属性声明 provider_id / provider_name。"""

    provider_id: str = ""    # 如 "douban"
    provider_name: str = ""  # 如 "豆瓣榜单"

    # 是否支持「搜索下载优先」：识别后先搜资源直接下载、失败再回退加订阅。
    # 仅少数来源（如豆瓣想看）需要，默认 False 走统一「加订阅」管线。
    supports_search_download: bool = False

    @abstractmethod
    def get_spec(self) -> "ProviderSpec":
        """返回本来源的元描述（含 options/filters schema）。"""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, options: dict, context: "ProviderContext") -> Iterator["RankMediaItem"]:
        """抓取+解析榜单，产出标准化条目（可携带宿主通用媒体身份）。

        以生成器 yield ``RankMediaItem``。单条解析失败应内部 try/except continue；
        整源抓取失败应向上抛出，由 runner 捕获处理。
        """
        raise NotImplementedError

    def has_listening(self, options: dict) -> bool:
        """给定 ``options`` 下本来源是否配置了「任何可监听内容」（启用后是否可能产出）。

        默认 ``True``；具有『空配置即空产出』语义的来源应重写。供保存时的「状态检测」在
        来源已启用却无任何监听内容时自动关闭其开关，避免空转（前端即时判断 + 后端保存兜底）。
        """
        return True
