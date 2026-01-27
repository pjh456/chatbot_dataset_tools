from .schema import APIConfig, ProcessingConfig, GlobalSettings
from .context import ConfigContext
from .manager import ConfigManager

config = ConfigManager()

__version__ = "0.5.0"
__all__ = [
    "config",
    "APIConfig",
    "ProcessingConfig",
    "GlobalSettings",
    "ConfigContext",
    "ConfigManager",
]
