from __future__ import annotations
from typing import Union, Iterable, overload, TYPE_CHECKING

from .message import Message
from .message_list import MessageList

if TYPE_CHECKING:
    from .lazy_message_view import LazyMessageView


class Conversation:
    def __init__(self, msgs: Iterable[Message] = []):
        self._data = MessageList(msgs)

    @property
    def messages(self) -> MessageList:
        return self._data

    def view(self):
        from .lazy_message_view import LazyMessageView

        return LazyMessageView(self._data)

    def __repr__(self):
        return f"Conversation({self._data!r})"

    def __str__(self):
        return f"<Conversation({len(self._data)} messages)>"

    @overload
    def __getitem__(self, idx: int) -> Message: ...

    @overload
    def __getitem__(self, idx: slice) -> Conversation: ...

    def __getitem__(self, idx: int | slice) -> Union[Message, Conversation]:
        result = self._data[idx]
        if isinstance(result, MessageList):
            return Conversation(result)
        return result
