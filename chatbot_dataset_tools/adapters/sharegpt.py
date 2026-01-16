from typing import List, Dict, Any, Optional
from chatbot_dataset_tools.core import Conversation, Message, Role, BaseAdapter


class ShareGPTAdapter(BaseAdapter):
    """ShareGPT 格式适配器.

    支持标准格式:
    {"conversations": [{"from": "human", "value": "hi"}, {"from": "gpt", "value": "hello"}], "system": "prompt"}
    """

    def __init__(self, role_map: Optional[Dict[str, Role]] = None):
        """初始化适配器.

        Args:
            role_map: 自定义角色映射表。默认为 human->USER, gpt->ASSISTANT, system->SYSTEM.
        """
        self.role_map = role_map or {
            "human": Role.USER,
            "user": Role.USER,
            "gpt": Role.ASSISTANT,
            "assistant": Role.ASSISTANT,
            "system": Role.SYSTEM,
            "chatgpt": Role.ASSISTANT,
            "bing": Role.ASSISTANT,
        }
        # 反向映射用于 dump
        self.rev_role_map = {v: k for k, v in self.role_map.items()}

    def load(self, data: List[Dict[str, Any]]) -> List[Conversation]:
        """将 ShareGPT 字典列表加载为 Conversation 模型列表.

        Args:
            data: 符合 ShareGPT 格式的原始列表.

        Returns:
            List[Conversation]: 中间模型列表.
        """
        results: List[Conversation] = []
        for entry in data:
            # 处理系统提示词
            sys_prompt: Optional[str] = entry.get("system", None)

            conv: Conversation = Conversation(
                id=entry.get("id", ""), system_prompt=sys_prompt
            )

            # 处理元数据
            for key, value in entry.items():
                if key not in ["conversations", "id", "system"]:
                    conv.char_metadata[key] = value

            # 处理对话项
            for msg_data in entry.get("conversations", []):
                raw_role: str = msg_data.get("from")
                content: str = msg_data.get("value", "")

                role = self.role_map.get(raw_role, Role.USER)

                # 这里暂不进行复杂的 Scene/Action 提取
                # 只是简单地填入 content。后续可以通过 Transform 模块提取。
                conv.add_message(role=role, content=content)

            results.append(conv)
        return results

    def dump(self, conversations: List[Conversation]) -> List[Dict[str, Any]]:
        """将内部模型导出为 ShareGPT 格式.

        Args:
            conversations: 内部模型列表.

        Returns:
            List[Dict[str, Any]]: ShareGPT 格式列表.
        """
        output = []
        for conv in conversations:
            entry = {"id": conv.id, "conversations": []}

            # 合并元数据
            entry.update(conv.char_metadata)

            for msg in conv.messages:
                # 渲染逻辑：导出到 ShareGPT 时，我们需要决定如何处理 action/thought
                # 这里展示一种简单的“合并”渲染，实际应用中可以配合 Renderer。
                final_value = self._simple_render(msg)

                entry["conversations"].append(
                    {
                        "from": self.rev_role_map.get(msg.role, "human"),
                        "value": final_value,
                    }
                )
            output.append(entry)
        return output

    def _simple_render(self, msg: Message) -> str:
        """简单的内部渲染，将 action 和 thought 合并到文本中."""
        parts = []
        if msg.thought:
            parts.append(f"<thought>\n{msg.thought}\n</thought>")
        if msg.action:
            parts.append(f"*{msg.action}*")
        parts.append(msg.content)
        return "\n".join(parts)
