from typing import Dict, Any, Optional
from chatbot_dataset_tools.core import Role, Message, Conversation
from chatbot_dataset_tools.api import APIClient
from .mapping import ResponseMapper


class DataSynthesizer:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def generate_conversation(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        mapper: ResponseMapper,
        world_info: Optional[str] = None,
    ) -> Optional[Conversation]:
        """通用生成逻辑：生成 -> 解析 -> 转换"""

        # 1. 调用 API 获取原始 JSON
        raw_json = self.api_client.generate_json(system_prompt, user_prompt, schema)
        if not raw_json:
            return None

        # 2. 根据 mapper 定位列表 (例如 raw_json['turns'])
        items = raw_json.get(mapper.items_path, [])
        if not items:
            return None

        conv = Conversation(world_definition=world_info)

        # 3. 核心解析逻辑：完全解耦字段名
        for item in items:
            # 根据 role_map 遍历该轮次中的所有角色消息
            for field_name, role_type in mapper.message_mapping.role_map.items():
                if field_name in item:
                    # 构造消息，这里还可以进一步扩展对 thought/action 的支持
                    msg = Message(
                        role=Role(role_type),
                        content=item[field_name],
                        # 如果有复杂的子字段定义，可以在这里处理
                    )
                    conv.messages.append(msg)

        return conv
