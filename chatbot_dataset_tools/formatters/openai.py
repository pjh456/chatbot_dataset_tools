from typing import Any, Dict, Optional
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

    def __init__(self, role_map: Optional[Dict[str, str]] = None):
        super().__init__(role_map)

    def format(self, conv: Conversation) -> Dict[str, Any]:
        messages = []
        for msg in conv.messages:
            messages.append(
                {"role": self.role_map.get(msg.role, msg.role), "content": msg.content}
            )
        return {"messages": messages}

    def parse(self, data: Dict[str, Any]) -> Conversation:
        raw_msgs = data.get("messages", [])
        rev_map = self._get_reverse_role_map()

        messages = []
        for m in raw_msgs:
            external_role: str = m.get("role", "")
            # 将外部名转回内部名
            internal_role: str = rev_map.get(external_role, external_role)
            messages.append(Message(role=internal_role, content=m.get("content", "")))

        return Conversation(messages)
