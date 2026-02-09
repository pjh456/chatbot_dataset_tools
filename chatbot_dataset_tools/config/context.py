from uuid import uuid4
from typing import Optional
from .schema import GlobalSettings


class ConfigContext:
    def __init__(
        self, settings: GlobalSettings, name: str = "default", uid: Optional[str] = None
    ):
        self.uid = uid or str(uuid4())
        self.name = name
        self.settings = settings

    def clone(self, name: Optional[str] = None, **changes) -> "ConfigContext":
        # 直接调用 settings 的深度衍生
        new_settings = self.settings.derive(**changes)
        return ConfigContext(new_settings, name=name or self.name)

    def __repr__(self):
        return f"<ConfigContext name={self.name} uid={self.uid[:8]}>"
