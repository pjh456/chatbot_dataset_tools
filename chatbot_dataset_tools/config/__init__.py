from .schema import APIConfig, HTTPConfig, ProcessingConfig, GlobalSettings
from .context import ConfigContext
from .manager import ConfigManager

config = ConfigManager()

__version__ = "0.5.4"
__all__ = [
    "config",
    "APIConfig",
    "HTTPConfig",
    "ProcessingConfig",
    "GlobalSettings",
    "ConfigContext",
    "ConfigManager",
]
