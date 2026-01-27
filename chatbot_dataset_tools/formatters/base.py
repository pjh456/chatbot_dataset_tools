import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from chatbot_dataset_tools.types import Conversation


@runtime_checkable
class Formatter(Protocol):
    def format(self, conv: Conversation) -> Any:
        """将对象转为字典/Json"""
        ...

    def parse(self, data: Any) -> Conversation:
        """将字典/Json 转回对象"""
        ...


class FieldMapper:
    """处理 ${key} 变量注入与提取的工具类"""

    @staticmethod
    def inject(template: str, variables: Dict[str, Any]) -> str:
        """将 ${var} 替换为实际值"""

        def replacer(match):
            key = match.group(1)
            return str(variables.get(key, match.group(0)))

        return re.sub(r"\$\{(.*?)\}", replacer, template)

    @staticmethod
    def extract(template: str, actual_str: str) -> Dict[str, str]:
        """从实际字符串中提取变量 (反向操作)"""
        # 将 ${var} 转为正则捕获组 (?P<var>.*?)
        pattern = re.escape(template).replace(r"\$\{", r"(?P<").replace(r"\}", r">.*?)")
        match = re.fullmatch(pattern, actual_str)
        return match.groupdict() if match else {}


class BaseFormatter(ABC):
    def __init__(self, role_map: Optional[Dict[str, str]] = None):
        # 如果构造时不传，则留空，后面动态去 config 拿
        self._role_map = role_map

    @property
    def role_map(self) -> Dict[str, str]:
        # 优先级：构造函数参数 > 当前全局配置上下文
        from chatbot_dataset_tools.config import config

        return self._role_map or config.settings.ds.role_map

    def _get_reverse_role_map(self) -> Dict[str, str]:
        return {v: k for k, v in self.role_map.items()}

    @abstractmethod
    def format(self, conv: Conversation) -> Any:
        """强制子类实现"""
        pass

    @abstractmethod
    def parse(self, data: Any) -> Conversation:
        """强制子类实现"""
        pass
