from __future__ import annotations
from typing import List, Union, overload
from dataclasses import dataclass
from .message import Message, MessageIt


@dataclass
class MessageList:
    messages: List[Message]

    def __init__(self, msgs: MessageIt = []):
        self.messages = list(msgs)

    def append(self, msg: Message) -> None:
        self.messages.append(msg)

    def extend(self, msgs: MessageIt) -> None:
        for msg in msgs:
            self.append(msg)

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)

    @overload
    def __getitem__(self, idx: int) -> Message: ...

    @overload
    def __getitem__(self, idx: slice) -> MessageList: ...

    def __getitem__(self, idx: slice | int) -> Union[Message, MessageList]:
        result = self.messages[idx]
        if isinstance(result, Message):
            return result
        return MessageList(result)

    def __setitem__(self, idx: int, value: Message) -> None:
        self.messages[idx] = value

    def __delitem__(self, idx: int) -> None:
        del self.messages[idx]

    def __add__(self, other: MessageIt) -> MessageList:
        return MessageList(self.messages + list(other))

    def __iadd__(self, other: MessageIt) -> MessageList:
        self.extend(other)
        return self

    def __mul__(self, n: int) -> MessageList:
        return MessageList(self.messages * n)

    __rmul__ = __mul__

    def last(self, n: int = 1) -> Message | MessageList:
        if n == 1:
            return self.messages[-1]
        return MessageList(self.messages[-n:])

    def copy(self) -> MessageList:
        return MessageList([msg.copy() for msg in self.messages])

    def __str__(self) -> str:
        return f"<MessageList({len(self)} messages)>"
