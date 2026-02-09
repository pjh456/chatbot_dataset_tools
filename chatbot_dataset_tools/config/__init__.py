from .schema import APIConfig, HTTPConfig, FileConfig, ProcessingConfig, GlobalSettings
from .context import ConfigContext
from .manager import ConfigManager

config = ConfigManager()

__version__ = "0.6.2"
__all__ = [
    "config",
    "APIConfig",
    "HTTPConfig",
    "FileConfig",
    "ProcessingConfig",
    "GlobalSettings",
    "ConfigContext",
    "ConfigManager",
]
