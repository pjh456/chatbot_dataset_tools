from typing import Any, Dict, Optional, Mapping
from .base import BaseFormatter
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.registry import register_formatter
from chatbot_dataset_tools.utils import get_logger

logger = get_logger(__name__)


@register_formatter()
class AlpacaFormatter(BaseFormatter):
    """
    {
        "instruction": "Explain quantum physics",
        "input": "",
        "output": "It's a branch of physics..."
    }
    """

    def __init__(self, role_map: Optional[Dict[str, str]] = None):
        super().__init__(role_map)

    def format(self, conv: Conversation) -> Dict[str, Any]:
        res = {"instruction": "", "input": "", "output": ""}

        # 将第一个 system 视为 instruction，第一个 user 视为 input，第一个 assistant 视为 output
        for msg in conv.messages:
            if msg.role == "system" and not res["instruction"]:
                res["instruction"] = msg.content
            elif msg.role == "user" and not res["input"]:
                res["input"] = msg.content
            elif msg.role == "assistant" and not res["output"]:
                res["output"] = msg.content

        # 如果没有 system，把 user 挪到 instruction
        if not res["instruction"] and res["input"]:
            res["instruction"] = res["input"]
            res["input"] = ""

        return res

    def parse(self, data: Mapping[str, Any]) -> Conversation:
        msgs = []
        inst = data.get("instruction", "")
        inp = data.get("input", "")
        out = data.get("output", "")

        # 数据完整性检查
        if not inst and not inp and not out:
            # 只有当全空时才警告，避免每条都刷屏
            # 记录数据片段方便 debug
            snippet = str(data)[:100]
            logger.warning(f"[Alpaca] Parsed empty conversation entry: {snippet}...")

        if inst and inp:
            msgs.append(Message("system", inst))
            msgs.append(Message("user", inp))
        elif inst:
            msgs.append(Message("user", inst))

        if out:
            msgs.append(Message("assistant", out))
        else:
            # TODO: 有些数据集可能只有 input 没有 output（用于推理），这里可以记录 debug
            pass

        return Conversation(msgs)
