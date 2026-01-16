from typing import List
from chatbot_dataset_tools.core import Message, BaseRenderer


class RolePlayRenderer(BaseRenderer):
    """通用角色扮演渲染器.

    支持自定义动作、思考、内容的包裹符号和排列顺序。
    """

    def __init__(
        self,
        thought_prefix: str = "<thought>\n",
        thought_suffix: str = "\n</thought>\n",
        action_prefix: str = "*",
        action_suffix: str = "* ",
        render_order: List[str] = ["thought", "action", "content"],
    ):
        """
        Args:
            thought_prefix: 思考内容的前缀.
            thought_suffix: 思考内容的后缀.
            action_prefix: 动作描写的前缀.
            action_suffix: 动作描写的后缀.
            render_order: 字段渲染的顺序，例如先渲染思考，再渲染动作，最后是正文.
        """
        self.thought_prefix = thought_prefix
        self.thought_suffix = thought_suffix
        self.action_prefix = action_prefix
        self.action_suffix = action_suffix
        self.render_order = render_order

    def render_message(self, message: Message) -> str:
        """根据配置的顺序和符号渲染消息."""
        parts = []
        for field in self.render_order:
            if field == "thought" and message.thought:
                parts.append(
                    f"{self.thought_prefix}{message.thought}{self.thought_suffix}"
                )
            elif field == "action" and message.action:
                parts.append(
                    f"{self.action_prefix}{message.action}{self.action_suffix}"
                )
            elif field == "content" and message.content:
                parts.append(message.content)
            elif field == "scene" and message.scene:
                # 场景通常渲染在最前面或作为旁白
                parts.insert(0, f"[{message.scene}] ")

        return "".join(parts).strip()
