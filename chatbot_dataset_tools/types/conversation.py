from __future__ import annotations
import hashlib
from typing import (
    Union,
    Iterable,
    Mapping,
    Dict,
    Optional,
    Any,
    overload,
    TYPE_CHECKING,
)
from dataclasses import dataclass, asdict, field
from .message import Message
from .message_list import MessageList

if TYPE_CHECKING:
    from .lazy_message_view import LazyMessageView


@dataclass
class Conversation:
    data: MessageList
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 内部缓存 UID，避免重复计算
    _cached_uid: Optional[str] = field(default=None, init=False, repr=False)

    def __init__(self, data: Iterable[Message] = [], meta: dict = {}):
        self.data = MessageList(data)
        self.metadata = meta
        self._cached_uid = None

    @property
    def messages(self) -> MessageList:
        return self.data

    @property
    def uid(self) -> str:
        return self.get_uid()

    def get_uid(self, force_recompute: bool = False) -> str:
        """
        获取对话的唯一标识符。

        逻辑：
        1. 返回 metadata['id'] 或 metadata['uid'] (如果存在)。
        2. 否则，根据消息内容生成 SHA-256 哈希。
        """
        if self._cached_uid and not force_recompute:
            return self._cached_uid

        # 1. 尝试从元数据获取显式 ID
        explicit_id = self.metadata.get("id") or self.metadata.get("uid")
        if explicit_id:
            self._cached_uid = str(explicit_id)
            return self._cached_uid

        # 2. 根据内容生成确定性哈希
        # 只哈希角色和内容，确保格式变动（如 metadata 其他字段变化）不影响身份识别
        content_buffer = []
        for msg in self.data:
            content_buffer.append(f"{msg.role}:{msg.content}")

        # 使用特定分隔符拼接，防止 ['a','bc'] 和 ['ab','c'] 碰撞
        fingerprint = "|".join(content_buffer).encode("utf-8")
        sha256_hash = hashlib.sha256(fingerprint).hexdigest()

        self._cached_uid = sha256_hash
        return self._cached_uid

    def view(self) -> LazyMessageView:
        from .lazy_message_view import LazyMessageView

        return LazyMessageView(self.data)

    @overload
    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "Conversation": ...

    @overload
    @classmethod
    def from_dict(
        cls,
        data: Iterable[Mapping[str, Any]],
    ) -> "Conversation": ...

    @classmethod
    def from_dict(cls, data) -> "Conversation":
        if isinstance(data, Mapping):
            messages_data = list(data.get("messages", []))
            metadata = data.get("metadata", {})
        else:
            messages_data = list(data)
            metadata = {}

        messages = [Message(**m) for m in messages_data]
        return cls(messages, metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {"messages": [asdict(m) for m in self.data], "metadata": self.metadata}

    def __str__(self) -> str:
        return f"<Conversation({len(self.data)} messages)>"

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        if not isinstance(other, Conversation):
            return False
        return self.uid == other.uid

    @overload
    def __getitem__(self, idx: int) -> Message: ...

    @overload
    def __getitem__(self, idx: slice) -> Conversation: ...

    def __getitem__(self, idx: int | slice) -> Union[Message, Conversation]:
        result = self.data[idx]
        if isinstance(result, MessageList):
            return Conversation(result)
        return result
