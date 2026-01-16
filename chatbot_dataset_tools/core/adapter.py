from typing import Any, List
from abc import ABC, abstractmethod
from .conversation import Conversation


class BaseAdapter(ABC):
    """数据集格式适配器基类.

    用于在 外部原始格式 (如 JSON 列表) 与 中间模型 (Conversation) 之间转换.
    """

    @abstractmethod
    def load(self, data: Any) -> List[Conversation]:
        """将外部格式加载为内部 Conversation 模型列表.

        Args:
            data: 原始数据，可以是 dict, list 或文件路径.

        Returns:
            List[Conversation]: 转换后的中间模型列表.
        """
        pass

    @abstractmethod
    def dump(self, conversations: List[Conversation]) -> Any:
        """将内部中间模型导出为目标格式数据.

        Args:
            conversations: 内部模型列表.

        Returns:
            Any: 目标格式的数据对象（如可序列化的 list 或 dict）.
        """
        pass
