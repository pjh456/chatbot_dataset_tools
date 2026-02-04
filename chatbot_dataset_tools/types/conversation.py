from __future__ import annotations
from typing import Union, Iterable, Mapping, Dict, List, Any, overload, TYPE_CHECKING
from dataclasses import dataclass, asdict, field
from .message import Message
from .message_list import MessageList

if TYPE_CHECKING:
    from .lazy_message_view import LazyMessageView


@dataclass
class Conversation:
    data: MessageList
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, data: Iterable[Message] = [], meta: dict = {}):
        self.data = MessageList(data)
        self.metadata = meta

    @property
    def messages(self) -> MessageList:
        return self.data

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

    @overload
    def __getitem__(self, idx: int) -> Message: ...

    @overload
    def __getitem__(self, idx: slice) -> Conversation: ...

    def __getitem__(self, idx: int | slice) -> Union[Message, Conversation]:
        result = self.data[idx]
        if isinstance(result, MessageList):
            return Conversation(result)
        return result
