from uuid import uuid4
from typing import Optional
from .schema import GlobalSettings
from dataclasses import replace, is_dataclass


class ConfigContext:
    def __init__(
        self, settings: GlobalSettings, name: str = "default", uid: Optional[str] = None
    ):
        self.uid = uid or str(uuid4())
        self.name = name
        self.settings = settings

    def clone(self, name: Optional[str] = None, **changes) -> "ConfigContext":
        """通过修改现有配置产生一个新的上下文"""
        updated_changes = {}

        for key, value in changes.items():
            # 获取当前设置中该字段的值
            current_field_value = getattr(self.settings, key)

            # 如果传入的是字典，且目标字段是一个 dataclass，则进行部分替换（Merge）
            if isinstance(value, dict) and is_dataclass(current_field_value):
                # 使用 replace 将字典里的内容注入到原有的 dataclass 对象中
                updated_changes[key] = replace(current_field_value, **value)  # type: ignore
            else:
                # 否则直接覆盖（比如用户传了一个完整的 APIConfig 对象）
                updated_changes[key] = value

        # 产生新的 settings 对象
        new_settings = replace(self.settings, **updated_changes)
        return ConfigContext(new_settings, name=name or self.name)

    def __repr__(self):
        return f"<ConfigContext name={self.name} uid={self.uid[:8]}>"
