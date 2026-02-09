from dataclasses import dataclass, field
from typing import Optional
from chatbot_dataset_tools.types import Conversation


@dataclass
class TaskResult:
    """包装单条数据的处理结果"""

    success: bool
    input: Conversation
    output: Optional[Conversation] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)  # 存储耗时、token 消耗等
