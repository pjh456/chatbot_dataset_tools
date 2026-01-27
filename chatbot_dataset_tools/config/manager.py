import contextvars
from typing import Dict, Optional
from contextlib import contextmanager
from .schema import GlobalSettings
from .context import ConfigContext

# 定义一个模块级的初始配置，作为所有线程的保底值
_ROOT_SETTINGS = GlobalSettings()
_ROOT_CONTEXT = ConfigContext(_ROOT_SETTINGS, name="default")


class ConfigManager:
    _instance = None
    # 存储所有注册过的上下文
    _registry: Dict[str, ConfigContext] = {}
    # 当前激活的上下文（线程/协程隔离）
    _active_cv: contextvars.ContextVar[ConfigContext] = contextvars.ContextVar(
        "active_config_context", default=_ROOT_CONTEXT
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 将根上下文注册到索引中
            cls._instance._registry["default"] = _ROOT_CONTEXT
            cls._instance._registry[_ROOT_CONTEXT.uid] = _ROOT_CONTEXT
        return cls._instance

    @property
    def current(self) -> ConfigContext:
        """获取当前活跃的上下文"""
        return self._active_cv.get()

    @property
    def settings(self) -> GlobalSettings:
        """便捷访问当前设置"""
        return self.current.settings

    def register(self, context: ConfigContext):
        """将一个上下文注册到全局索引中"""
        self._registry[context.uid] = context
        self._registry[context.name] = context

    def get_context(self, identifier: str) -> Optional[ConfigContext]:
        return self._registry.get(identifier)

    @contextmanager
    def switch(
        self, identifier: ConfigContext | Optional[str] = None, **temporary_changes
    ):
        """
        核心方法：切换上下文。
        1. 如果传了 identifier，则切换到对应的已注册上下文
        2. 如果传了 temporary_changes，则在当前基础上做临时修改
        """
        # 如果 identifier 本身就是 ConfigContext 对象，直接使用它
        if isinstance(identifier, ConfigContext):
            base_ctx = identifier
        else:
            base_ctx = (
                self.get_context(identifier) if identifier else self.current
            ) or self.current

        if temporary_changes:
            # 临时产生一个新的匿名上下文
            target_ctx = base_ctx.clone(name="_temp", **temporary_changes)
        else:
            target_ctx = base_ctx

        token = self._active_cv.set(target_ctx)
        try:
            yield target_ctx
        finally:
            self._active_cv.reset(token)

    def set_global_default(self, identifier: str):
        """永久切换全局默认配置"""
        ctx = self.get_context(identifier)
        if ctx:
            self._active_cv.set(ctx)
