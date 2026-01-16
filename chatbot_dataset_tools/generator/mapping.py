from typing import Dict, Optional
from pydantic import BaseModel, Field


class MessageMapping(BaseModel):
    """描述单个对话轮次中字段的映射关系"""

    role_map: Dict[str, str] = Field(
        ...,
        description="JSON字段名到角色的映射，例如 {'user_msg': 'user', 'resp': 'assistant'}",
    )

    # 可选：支持将特定字段提取为 thought/action
    thought_field: Optional[str] = None
    action_field: Optional[str] = None
    content_field: Optional[str] = (
        None  # 如果 role_map 已经定义了角色，这里通常用于更复杂的解析
    )


class ResponseMapper(BaseModel):
    """描述整个 JSON 响应的结构"""

    items_path: str = "turns"  # 列表所在的字段名
    message_mapping: MessageMapping
