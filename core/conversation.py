from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .role import Role
from .message import Message


class Conversation(BaseModel):
    """完整的对话会话模型.

    Attributes:
        id (str): 对话的唯一标识符.
        messages (List[Message]): 消息列表，按时间顺序排列.
        system_prompt (Optional[str]): 顶层的系统提示词（若不放在messages首条时使用）.
        world_definition (Optional[str]): 全局世界观/设定背景.
        char_metadata (Dict[str, Any]): 角色信息，如姓名、性格标签、好感度等.
    """

    id: str = Field(default_factory=str, description="会话ID")

    messages: List[Message] = Field(default_factory=list, description="对话消息流")
    system_prompt: Optional[str] = Field(None, description="全局系统提示词")
    world_definition: Optional[str] = Field(None, description="世界观/设定")

    char_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="角色属性元数据"
    )

    def add_message(self, role: Role, content: str, **kwargs) -> Message:
        """快捷向对话中添加一条消息.

        Args:
            role: 角色枚举.
            content: 对话文本.
            **kwargs: 传入 thought, action, scene 或 metadata.

        Returns:
            Message: 创建的消息实例.
        """
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        return msg
