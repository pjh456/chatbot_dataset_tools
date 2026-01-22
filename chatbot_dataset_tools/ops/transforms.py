from typing import Callable, Dict
from chatbot_dataset_tools.types import Message, Conversation


def rename_roles(mapping: Dict[str, str]) -> Callable[[Conversation], Conversation]:
    """重命名角色名称"""

    def _transform(conv: Conversation) -> Conversation:
        for m in conv.messages:
            if m.role in mapping:
                m.role = mapping[m.role]
        return conv

    return _transform


def strip_content() -> Callable[[Conversation], Conversation]:
    """去除所有消息首尾空白"""

    def _transform(conv: Conversation) -> Conversation:
        for m in conv.messages:
            m.content = m.content.strip()
        return conv

    return _transform


def merge_consecutive_roles(sep: str = "\n") -> Callable[[Conversation], Conversation]:
    """合并连续出现的同角色消息（比如两个 user 连续发消息）"""

    def _transform(conv: Conversation) -> Conversation:
        if not conv.messages:
            return conv

        new_msgs = []
        current_msg = conv.messages[0].copy()

        for next_msg in conv.messages[1:]:
            if next_msg.role == current_msg.role:
                current_msg.content += sep + next_msg.content
            else:
                new_msgs.append(current_msg)
                current_msg = next_msg.copy()

        new_msgs.append(current_msg)
        conv.data.messages = new_msgs  # 直接更新内部 MessageList
        return conv

    return _transform


def limit_context(max_messages: int) -> Callable[[Conversation], Conversation]:
    """限制对话历史长度，只保留最后的 N 条消息"""

    def _transform(conv: Conversation) -> Conversation:
        if len(conv.messages) > max_messages:
            conv.data = conv.data.last(max_messages)
        return conv

    return _transform


def remove_system_message() -> Callable[[Conversation], Conversation]:
    """移除所有的系统提示词（role='system'）"""

    def _transform(conv: Conversation) -> Conversation:
        conv.data.messages = [m for m in conv.messages if m.role != "system"]
        return conv

    return _transform
