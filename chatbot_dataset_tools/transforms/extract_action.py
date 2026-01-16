import re
from chatbot_dataset_tools.core import Conversation, BaseTransform


class ExtractActionTransform(BaseTransform):
    """自动从 content 中提取用星号 *括起来* 的动作."""

    def apply(self, conversation: Conversation) -> Conversation:
        for msg in conversation.messages:
            # 匹配 *动作* 内容
            actions = re.findall(r"\*(.*?)\*", msg.content)
            if actions:
                # 将提取到的第一个动作存入 action 字段
                msg.action = actions[0]
                # 从 content 中移除 *动作* 文本
                msg.content = re.sub(r"\*.*?\*", "", msg.content).strip()
        return conversation
