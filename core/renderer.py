from abc import ABC, abstractmethod
from .message import Message


class BaseRenderer(ABC):
    """文本渲染器基类.

    用于将结构化的 Message 或 Conversation 渲染为最终微调所需的纯文本格式.
    """

    @abstractmethod
    def render_message(self, message: Message) -> str:
        """渲染整条对话.

        Args:
            conversation: 待渲染的对话模型.

        Returns:
            Any: 渲染后的结果（通常是字符串或特定格式的 dict）.
        """
        pass
