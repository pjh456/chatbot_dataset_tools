import httpx
from typing import Optional, Dict, Any
from .base import BaseProcessor
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.formatters.base import FieldMapper
from chatbot_dataset_tools.config import config, APIConfig


class LLMProcessor(BaseProcessor):
    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        user_prompt_template: str = "${content}",  # 支持变量注入
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        api_cfg: Optional[APIConfig] = None,
    ):
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.model = model
        self.temperature = temperature
        # 允许实例级覆盖 API 配置，否则使用全局
        self._api_cfg = api_cfg

    @property
    def api_config(self) -> APIConfig:
        return self._api_cfg or config.settings.api

    def _build_payload(self, conv: Conversation) -> Dict[str, Any]:
        """构建 OpenAI 格式的请求体"""
        # 提取变量 (简单实现：提取最后一条用户的消息内容)
        # TODO: 扩展这里的逻辑，比如提取 metadata
        last_user_msg = next(
            (m for m in reversed(conv.messages) if m.role == "user"), None
        )
        variables = {
            "content": last_user_msg.content if last_user_msg else "",
            **conv.metadata,  # 允许 metadata 里的字段也注入到 prompt
        }

        # 2. 渲染模板
        rendered_content = FieldMapper.inject(self.user_prompt_template, variables)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": rendered_content},
        ]

        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }

    def process(self, conv: Conversation) -> Optional[Conversation]:
        """执行 API 调用"""
        cfg = self.api_config

        # 简单的 httpx 同步调用 (TaskRunner 会在线程池里跑它，所以这里同步没问题)
        # 要求为 OpenAI 兼容接口
        headers = {
            "Authorization": f"Bearer {cfg.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = self._build_payload(conv)

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{cfg.openai_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                # 解析响应
                content = data["choices"][0]["message"]["content"]

                # 构造新的 Conversation，克隆原对话并追加 assistant 回复
                new_msgs = [m.copy() for m in conv.messages]
                new_msgs.append(Message(role="assistant", content=content))

                # 记录 Token 消耗到 metadata
                usage = data.get("usage", {})
                new_meta = conv.metadata.copy()
                new_meta.update({"usage": usage})

                return Conversation(new_msgs, meta=new_meta)

        except Exception as e:
            # TaskRunner 会捕获这个异常并根据 ignore_errors 处理
            raise RuntimeError(f"API Call Failed: {str(e)}")
