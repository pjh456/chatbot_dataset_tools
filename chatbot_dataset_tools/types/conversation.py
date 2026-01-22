from __future__ import annotations
from typing import Union, Iterable, overload, TYPE_CHECKING
from dataclasses import dataclass, asdict, field
from .message import Message
from .message_list import MessageList

if TYPE_CHECKING:
    from .lazy_message_view import LazyMessageView


@dataclass
class Conversation:
    data: MessageList
    metadata: dict = field(default_factory=dict)

    def __init__(self, data: Iterable[Message] = [], meta: dict = {}):
        self.data = MessageList(data)
        self.metadata = meta

    @property
    def messages(self) -> MessageList:
        return self.data

    def view(self) -> LazyMessageView:
        from .lazy_message_view import LazyMessageView

        return LazyMessageView(self.data)

    @classmethod
    def from_dict(cls, data: dict):
        messages = [Message(**m) for m in data.get("messages", [])]
        return cls(messages, data.get("metadata", {}))

    def to_dict(self):
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
