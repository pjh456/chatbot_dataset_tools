from typing import Callable, Dict, Optional
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import config


def rename_roles(
    mapping: Optional[Dict[str, str]] = None,
) -> Callable[[Conversation], Conversation]:
    """重命名角色名称"""

    def _transform(conv: Conversation) -> Conversation:
        actual_map = mapping or config.settings.ds.role_map

        for m in conv.messages:
            if m.role in actual_map:
                m.role = actual_map[m.role]
        return conv

    return _transform


def strip_content() -> Callable[[Conversation], Conversation]:
    """去除所有消息首尾空白"""

    def _transform(conv: Conversation) -> Conversation:
        for m in conv.messages:
            m.content = m.content.strip()
        return conv

    return _transform


def merge_consecutive_roles(
    sep: Optional[str] = "\n",
) -> Callable[[Conversation], Conversation]:
    """合并连续出现的同角色消息（比如两个 user 连续发消息）"""

    def _transform(conv: Conversation) -> Conversation:
        actual_sep = sep or config.settings.ds.msg_sep

        if not conv.messages:
            return conv

        new_msgs = []
        current_msg = conv.messages[0].copy()

        for next_msg in conv.messages[1:]:
            if next_msg.role == current_msg.role:
                current_msg.content += actual_sep + next_msg.content
            else:
                new_msgs.append(current_msg)
                current_msg = next_msg.copy()

        new_msgs.append(current_msg)
        conv.data.messages = new_msgs
        return conv

    return _transform


def limit_context(max_messages: int) -> Callable[[Conversation], Conversation]:
    """限制对话历史长度，只保留最后的 N 条消息"""

    def _transform(conv: Conversation) -> Conversation:
        # 这里预留一个从 proc 配置读取的逻辑（如果有的话）
        actual_max = max_messages or getattr(
            config.settings.proc, "max_context_len", 999999
        )

        if len(conv.messages) > actual_max:
            conv.data = conv.data.last(actual_max)
        return conv

    return _transform


def remove_system_message(
    role: Optional[str] = None,
) -> Callable[[Conversation], Conversation]:
    """移除所有的系统提示词（role='system'）"""

    def _transform(conv: Conversation) -> Conversation:
        # 优先使用参数指定的 role，否则去配置里找 ds.role_map 里的 system 定义
        sys_role = role or config.settings.ds.role_map.get("system", "system")
        conv.data.messages = [m for m in conv.messages if m.role != sys_role]
        return conv

    return _transform
