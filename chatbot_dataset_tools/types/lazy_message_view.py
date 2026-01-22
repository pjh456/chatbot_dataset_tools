from __future__ import annotations
from typing import Callable, List, TypeAlias, TYPE_CHECKING
from .message import Message, MessageIt
from .message_list import MessageList

if TYPE_CHECKING:
    from .conversation import Conversation

MessageOp: TypeAlias = Callable[[MessageIt], MessageIt]
MessageOpList: TypeAlias = List[MessageOp]


class LazyMessageView:
    def __init__(
        self,
        source: MessageList,
        ops: MessageOpList = [],
    ):
        self._source: MessageList = source
        self._ops: MessageOpList = ops

    def _iter(self) -> MessageIt:
        msgs: MessageIt = iter(self._source)
        for op in self._ops:
            msgs = op(msgs)
        return msgs

    def map(self, func: Callable[[Message], Message]) -> LazyMessageView:
        return LazyMessageView(
            self._source, self._ops + [lambda msgs: (func(m) for m in msgs)]
        )

    def filter(self, func: Callable[["Message"], bool]) -> LazyMessageView:
        return LazyMessageView(
            self._source, self._ops + [lambda msgs: (m for m in msgs if func(m))]
        )

    def to_list(self) -> List[Message]:
        return list(self._iter())

    def to_message_list(self) -> MessageList:
        return MessageList(self._iter())

    def to_conversation(self) -> Conversation:
        from .conversation import Conversation

        return Conversation(self.to_message_list())

    def __iter__(self):
        return self._iter()

    def __len__(self):
        # 注意：惰性视图需要遍历来计算长度
        return sum(1 for _ in self._iter())

    def __getitem__(self, idx: int | slice):
        msgs = self.to_list()
        result = msgs[idx]
        if isinstance(result, List):
            return LazyMessageView(MessageList(result))
        return result

    def __repr__(self):
        return f"LazyMessageView({self.to_list()!r})"

    def __str__(self):
        return f"<LazyMessageView({len(self)} messages)>"
