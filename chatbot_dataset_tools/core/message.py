from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .role import Role


class Message(BaseModel):
    """单条消息模型，支持角色扮演的高级字段.

    Attributes:
        role (Role): 消息发送者的角色类型.
        content (str): 角色实际说出的文本内容.
        thought (Optional[str]): 内部思考过程 (Chain-of-Thought)，训练时可选择隐藏或保留.
        action (Optional[str]): 行为描写，如 *轻轻推门进来* 或 [坐下].
        scene (Optional[str]): 局部场景描述或环境状态变化.
        metadata (Dict[str, Any]): 扩展字段，用于存储原格式中不通用的杂项数据.
    """

    role: Role = Field(..., description="角色类型")
    content: str = Field(default="", description="对话文本内容")

    thought: Optional[str] = Field(default=None, description="模型的内心活动/思维链")
    action: Optional[str] = Field(default=None, description="角色的动作/表情/神态描写")
    scene: Optional[str] = Field(
        default=None, description="当前消息发生的特定场景上下文"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="原始数据的额外元信息"
    )

    model_config = ConfigDict(frozen=False, extra="allow")

    def __str__(self) -> str:
        """返回格式化的消息摘要，方便调试打印."""
        return (
            f"[{self.role.value}] action={self.action} content={self.content[:20]}..."
        )

    def clone(self) -> "Message":
        """执行消息的深拷贝.

        Returns:
            Message: 拥有独立内存地址的新消息对象，修改它不会影响原对象.
        """
        return self.model_copy(deep=True)
