from typing import Callable, Iterable
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.registry import register_filter


@register_filter()
def min_turns(n: int) -> Callable[[Conversation], bool]:
    """至少有 n 轮对话"""
    return lambda conv: len(conv.messages) >= n


@register_filter()
def max_turns(n: int) -> Callable[[Conversation], bool]:
    """至多有 n 轮对话"""
    return lambda conv: len(conv.messages) <= n


@register_filter()
def has_turns_in(min: int, max: int) -> Callable[[Conversation], bool]:
    """对话数量在 [min, max] 内"""
    return lambda conv: min_turns(min)(conv) and max_turns(max)(conv)


@register_filter()
def has_role(role: str) -> Callable[[Conversation], bool]:
    """对话中必须包含某个角色"""
    return lambda conv: any(m.role == role for m in conv.messages)


@register_filter()
def has_roles(roles: Iterable[str]) -> Callable[[Conversation], bool]:
    """对话中必须包含列表里的所有角色"""
    return lambda conv: all(
        any(m.role == role for m in conv.messages) for role in roles
    )


@register_filter()
def content_contains(
    text: str, case_sensitive: bool = False
) -> Callable[[Conversation], bool]:
    """消息内容包含特定文本"""

    def _filter(conv: Conversation) -> bool:
        for m in conv.messages:
            content = m.content if case_sensitive else m.content.lower()
            target = text if case_sensitive else text.lower()
            if target in content:
                return True
        return False

    return _filter


@register_filter()
def is_valid_alternating() -> Callable[[Conversation], bool]:
    """检查是否是严格的 user/assistant 交替出现"""

    def _filter(conv: Conversation) -> bool:
        if not conv.messages:
            return False

        role_map = config.settings.ds.role_map

        # 过滤掉系统消息后检查交替
        relevant_messages = [
            m for m in conv.messages if m.role != role_map.get("system", "system")
        ]
        if not relevant_messages:
            return False

        roles = [m.role for m in relevant_messages]
        for i in range(len(roles) - 1):
            if roles[i] == roles[i + 1]:
                return False
        return True

    return _filter
