# chatbot_dataset_tools/tasks/processor.py
from abc import ABC, abstractmethod
from typing import Optional
from chatbot_dataset_tools.types import Conversation


class BaseProcessor(ABC):
    """算子处理器基类"""

    @abstractmethod
    def process(self, conv: Conversation) -> Optional[Conversation]:
        """
        核心逻辑：输入一个对话，返回处理后的对话。
        如果返回 None，表示该条数据被舍弃。
        """
        raise NotImplementedError

    def __call__(self, conv: Conversation) -> Optional[Conversation]:
        return self.process(conv)
