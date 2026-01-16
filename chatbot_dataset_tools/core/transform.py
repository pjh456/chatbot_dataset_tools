from abc import ABC, abstractmethod
from .conversation import Conversation


class BaseTransform(ABC):
    """对话变换器基类.

    用于对 Conversation 进行结构化调整，如清洗、剪枝、合并等.
    """

    @abstractmethod
    def apply(self, conversation: Conversation) -> Conversation:
        """执行变换逻辑.

        Args:
            conversation: 原始对话模型.

        Returns:
            Conversation: 变换后的对话模型.

        建议实现：
            def apply(self, conversation: Conversation) -> Conversation:
                new_conv = conversation.copy()  # 先拷贝
                do_something() # ... 对 new_conv 进行操作
                return new_conv
        """
        pass
