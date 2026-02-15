from .schema import (
    BaseConfig,
    APIConfig,
    ProcessingConfig,
    FileConfig,
    HTTPConfig,
    TaskConfig,
    GlobalSettings,
)
from .context import ConfigContext
from .manager import ConfigManager

config = ConfigManager()

__version__ = "0.7.6"
__all__ = [
    "config",
    "BaseConfig",
    "APIConfig",
    "ProcessingConfig",
    "FileConfig",
    "HTTPConfig",
    "TaskConfig",
    "GlobalSettings",
    "ConfigContext",
    "ConfigManager",
]
