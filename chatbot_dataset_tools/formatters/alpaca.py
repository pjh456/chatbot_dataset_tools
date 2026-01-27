from typing import Any, Dict
from .base import BaseFormatter
from chatbot_dataset_tools.types import Message, Conversation


class AlpacaFormatter(BaseFormatter):
    """
    {
        "instruction": "Explain quantum physics",
        "input": "",
        "output": "It's a branch of physics..."
    }
    """

    def format(self, conv: Conversation) -> Dict[str, Any]:
        res = {"instruction": "", "input": "", "output": ""}

        # 逻辑：将第一个 system 视为 instruction，第一个 user 视为 input，第一个 assistant 视为 output
        # 这是一种常见的平铺方式
        for msg in conv.messages:
            if msg.role == "system" and not res["instruction"]:
                res["instruction"] = msg.content
            elif msg.role == "user" and not res["input"]:
                res["input"] = msg.content
            elif msg.role == "assistant" and not res["output"]:
                res["output"] = msg.content

        # 如果没有 system，把 user 挪到 instruction 也是一种常见做法
        if not res["instruction"] and res["input"]:
            res["instruction"] = res["input"]
            res["input"] = ""

        return res

    def parse(self, data: Dict[str, Any]) -> Conversation:
        msgs = []
        inst = data.get("instruction", "")
        inp = data.get("input", "")
        out = data.get("output", "")

        if inst and inp:
            msgs.append(Message("system", inst))
            msgs.append(Message("user", inp))
        elif inst:
            msgs.append(Message("user", inst))

        if out:
            msgs.append(Message("assistant", out))

        return Conversation(msgs)
