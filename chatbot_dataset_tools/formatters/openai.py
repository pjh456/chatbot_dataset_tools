from typing import Any, Dict
from .base import BaseFormatter
from chatbot_dataset_tools.types import Message, Conversation


class OpenAIFormatter(BaseFormatter):
    """
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """

    # OpenAI 的角色名通常就是标准名，不需要映射，但为了严谨我们可以写一下
    role_map = {"user": "user", "assistant": "assistant", "system": "system"}

    def format(self, conv: Conversation) -> Dict[str, Any]:
        messages = []
        for msg in conv.messages:
            messages.append(
                {"role": self.role_map.get(msg.role, msg.role), "content": msg.content}
            )
        return {"messages": messages}

    def parse(self, data: Dict[str, Any]) -> Conversation:
        raw_msgs = data.get("messages", [])
        messages = [Message(role=m["role"], content=m["content"]) for m in raw_msgs]
        return Conversation(messages)
