from typing import Any, Dict, Optional, Mapping
from .base import BaseFormatter
from chatbot_dataset_tools.types import Message, Conversation


class ShareGPTFormatter(BaseFormatter):
    """
    {
        "conversations": [
            {"from": "human", "value": "hi"},
            {"from": "gpt", "value": "hello"}
        ],
        "metadata": {...}
    }
    """

    def __init__(self, role_map: Optional[Dict[str, str]] = None):
        super().__init__(role_map)

    def format(self, conv: Conversation) -> Dict[str, Any]:
        conv_list = []
        for msg in conv.messages:
            conv_list.append(
                {"from": self.role_map.get(msg.role, msg.role), "value": msg.content}
            )

        res: Dict[str, Any] = {"conversations": conv_list}
        if conv.metadata:
            res["metadata"] = conv.metadata
        return res

    def parse(self, data: Mapping[str, Any]) -> Conversation:
        rev_map = self._get_reverse_role_map()
        raw_msgs = data.get("conversations", [])

        messages = []
        for m in raw_msgs:
            role: str = m.get("from", "user")
            content = m.get("value", "")
            messages.append(Message(role=rev_map.get(role, role), content=content))

        metadata = data.get("metadata", {})
        return Conversation(messages, metadata)
