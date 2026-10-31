"""来源实现包：导入各 provider 模块以触发 ``@register`` 注册。

registry 单例通过导入副作用收集所有 Provider 类，供插件主体 ``registry.create_all()`` /
``registry.get()`` 使用。新增来源时在此追加一行 ``from . import <module>`` 即可。

本插件聚合的来源：
- douban / maoyan / mikan / netflix：公开榜单
- popular：热门媒体（MoviePilot 服务端订阅统计，即「热门媒体订阅」）
- douban_want：豆瓣想看（用户个人「想看」RSS）
"""
from . import douban, maoyan, popular, mikan, netflix, douban_want  # noqa: F401 - 导入触发 @register 注册
