import importlib
import pkgutil
import logging
from typing import List
from types import ModuleType

logger = logging.getLogger(__name__)


def import_module_from_string(name: str) -> ModuleType:
    """
    根据字符串导入模块。
    例如: "my_project.custom_ops"
    """
    try:
        return importlib.import_module(name)
    except ImportError as e:
        logger.error(f"Failed to import module '{name}': {e}")
        raise


def import_submodules(package_name: str, recursive: bool = True) -> List[ModuleType]:
    """
    递归导入一个包下的所有子模块。

    Args:
        package_name: 包名，例如 "chatbot_dataset_tools.ops"
        recursive: 是否递归导入子包
    """
    results = []

    # 1. 先导入顶层包
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.warning(f"Could not import package '{package_name}': {e}")
        return []

    results.append(package)

    # 2. 如果它没有 __path__ 属性，说明它是个单文件模块，不是包，直接返回
    if not hasattr(package, "__path__"):
        return results

    # 3. 遍历包下的所有模块
    # pkgutil.walk_packages 会自动处理递归
    if recursive:
        scanner = pkgutil.walk_packages(package.__path__, package.__name__ + ".")
    else:
        scanner = pkgutil.iter_modules(package.__path__, package.__name__ + ".")

    for _, name, is_pkg in scanner:
        try:
            # 这里的 name 已经是完整的路径了，如 "chatbot_dataset_tools.ops.filters"
            module = importlib.import_module(name)
            results.append(module)
            logger.debug(f"Auto-imported: {name}")
        except ImportError as e:
            logger.warning(f"Failed to auto-import '{name}': {e}")

    return results


def autodiscover_internal_components():
    """
    自动扫描并导入框架内部的核心组件。
    不需要再手动 import chatbot_dataset_tools.ops.filters 了。
    """
    # 这里定义自动扫描的内部包路径
    INTERNAL_PACKAGES = [
        "chatbot_dataset_tools.types",
        "chatbot_dataset_tools.config",
        "chatbot_dataset_tools.connectors",
        "chatbot_dataset_tools.datasets",
        "chatbot_dataset_tools.ops",
        "chatbot_dataset_tools.formatters",
        "chatbot_dataset_tools.tasks",
        "chatbot_dataset_tools.registry",
    ]

    count = 0
    for pkg in INTERNAL_PACKAGES:
        modules = import_submodules(pkg)
        count += len(modules)

    logger.info(f"Registry Autodiscovery: Scanned {count} internal modules.")
