from .roleplay import RolePlayRenderer


class RendererPresets:
    """常用渲染器预设."""

    @staticmethod
    def classic_asterisk():
        """经典星号风格: *动作*对话"""
        return RolePlayRenderer(action_prefix="*", action_suffix="*")

    @staticmethod
    def bracket_style():
        """括号风格: (动作)对话"""
        return RolePlayRenderer(action_prefix="(", action_suffix=")")

    @staticmethod
    def thought_chain():
        """带深度思考的风格: <thought>...</thought>*动作*对话"""
        return RolePlayRenderer(
            thought_prefix="<thought>\n",
            thought_suffix="\n</thought>\n",
            action_prefix="*",
            action_suffix="*",
        )
