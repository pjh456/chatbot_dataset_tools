from __future__ import annotations
from typing import List, Union, overload

from .message import Message, MessageIt


class MessageList:
    def __init__(self, msgs: MessageIt = []):
        self._msgs: List[Message] = list(msgs)

    def append(self, msg: Message) -> None:
        self._msgs.append(msg)

    def extend(self, msgs: MessageIt) -> None:
        for msg in msgs:
            self.append(msg)

    def __len__(self) -> int:
        return len(self._msgs)

    def __iter__(self):
        return iter(self._msgs)

    @overload
    def __getitem__(self, idx: int) -> Message: ...

    @overload
    def __getitem__(self, idx: slice) -> MessageList: ...

    def __getitem__(self, idx: slice | int) -> Union[Message, MessageList]:
        result = self._msgs[idx]
        if isinstance(result, Message):
            return result
        return MessageList(result)

    def __setitem__(self, idx: int, value: Message) -> None:
        self._msgs[idx] = value

    def __delitem__(self, idx: int) -> None:
        del self._msgs[idx]

    def __add__(self, other: MessageIt) -> MessageList:
        return MessageList(self._msgs + list(other))

    def __iadd__(self, other: MessageIt) -> MessageList:
        self.extend(other)
        return self

    def __mul__(self, n: int) -> MessageList:
        return MessageList(self._msgs * n)

    __rmul__ = __mul__

    def last(self, n: int = 1) -> Message | MessageList:
        if n == 1:
            return self._msgs[-1]
        return MessageList(self._msgs[-n:])

    def copy(self) -> MessageList:
        return MessageList([msg.copy() for msg in self._msgs])

    def __repr__(self) -> str:
        return f"MessageList({self._msgs!r})"

    def __str__(self) -> str:
        return f"<MessageList({len(self)} messages)>"
