from dataclasses import dataclass, field
from typing import Iterable, TypeAlias


@dataclass
class Message:
    role: str
    content: str = ""
    metadata: dict = field(default_factory=dict)

    def __str__(self):
        return f"[{self.role}] {self.content}"

    def __repr__(self):
        return f"Message(role={self.role!r}, content={self.content!r})"

    def copy(self) -> "Message":
        """创建消息副本，不绑定原始容器"""
        return Message(
            role=self.role,
            content=self.content,
        )


MessageIt: TypeAlias = Iterable[Message]
