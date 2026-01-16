from typing import List, Dict, Any, Optional
from chatbot_dataset_tools.core import (
    Role,
    Conversation,
    BaseAdapter,
    BaseRenderer,
)
from chatbot_dataset_tools.renderers import RolePlayRenderer


class AlpacaAdapter(BaseAdapter):
    """完善的 Alpaca 格式适配器.

    支持格式：
    1. 标准单轮: instruction, input, output
    2. LLaMA Factory 多轮扩展: instruction, input, output, history, system (可选)

    history 格式约定: [[user_1, assistant_1], [user_2, assistant_2], ...]
    """

    def __init__(
        self,
        renderer: Optional[BaseRenderer] = None,
        use_history: bool = True,
        system_field: str = "system",
    ):
        """
        Args:
            renderer: 渲染器，用于将结构化字段转为文本。
            use_history: 导出时是否使用 history 字段存储多轮对话。
                         若为 False，则将历史记录压缩进 instruction。
            system_field: 存储系统提示词的字段名，默认为 "system"。
        """
        self.renderer = renderer or RolePlayRenderer()
        self.use_history = use_history
        self.system_field = system_field

    def load(self, data: List[Dict[str, Any]]) -> List[Conversation]:
        """从 Alpaca 字典列表加载为内部模型."""
        results = []
        for entry in data:
            conv = Conversation(id=entry.get("id", ""))

            # 1. 提取系统提示词
            if self.system_field in entry:
                conv.system_prompt = entry[self.system_field]

            # 2. 提取历史记录 (history: [[u1, a1], [u2, a2]])
            history: List[List[str]] = entry.get("history", [])
            for pair in history:
                if len(pair) == 2:
                    conv.add_message(Role.USER, content=pair[0])
                    conv.add_message(Role.ASSISTANT, content=pair[1])

            # 3. 提取当前轮次
            inst = entry.get("instruction", "")
            inp = entry.get("input", "")
            # 合并 instruction 和 input
            current_user_text = f"{inst}\n{inp}".strip() if inp else inst

            conv.add_message(Role.USER, content=current_user_text)
            conv.add_message(Role.ASSISTANT, content=entry.get("output", ""))

            # 4. 存储其余元数据
            reserved_keys = [
                "instruction",
                "input",
                "output",
                "history",
                self.system_field,
                "id",
            ]
            for k, v in entry.items():
                if k not in reserved_keys:
                    conv.char_metadata[k] = v

            results.append(conv)
        return results

    def dump(self, conversations: List[Conversation]) -> List[Dict[str, Any]]:
        """将内部模型导出为 Alpaca 风格的字典列表."""
        output = []
        for conv in conversations:
            if len(conv.messages) < 2:
                continue

            # 获取最后一轮对话
            last_assistant_msg = conv.messages[-1]
            last_user_msg = conv.messages[-2]

            if last_assistant_msg.role != Role.ASSISTANT:
                continue

            entry = {}
            # 处理 ID 和 元数据
            if conv.id:
                entry["id"] = conv.id
            entry.update(conv.char_metadata)

            # 处理系统提示词
            if conv.system_prompt:
                entry[self.system_field] = conv.system_prompt

            if self.use_history:
                # --- LLaMA Factory 风格：使用 history 字段 ---
                entry["instruction"] = self.renderer.render_message(last_user_msg)
                entry["input"] = ""
                entry["output"] = self.renderer.render_message(last_assistant_msg)

                # 提取历史（排除最后两项）
                history_list = []
                # 按对提取历史消息
                history_messages = conv.messages[:-2]
                for i in range(0, len(history_messages) - 1, 2):
                    u_msg = history_messages[i]
                    a_msg = history_messages[i + 1]
                    if u_msg.role == Role.USER and a_msg.role == Role.ASSISTANT:
                        history_list.append(
                            [
                                self.renderer.render_message(u_msg),
                                self.renderer.render_message(a_msg),
                            ]
                        )
                entry["history"] = history_list
            else:
                # --- 标准 Alpaca 风格：上下文全压缩进 instruction ---
                context_texts = []
                # 历史消息（除去最后一轮）全部渲染并连接
                for msg in conv.messages[:-1]:
                    prefix = "User: " if msg.role == Role.USER else "Assistant: "
                    context_texts.append(f"{prefix}{self.renderer.render_message(msg)}")

                entry["instruction"] = "\n".join(context_texts)
                entry["input"] = ""
                entry["output"] = self.renderer.render_message(last_assistant_msg)
                entry["history"] = []

            output.append(entry)
        return output
