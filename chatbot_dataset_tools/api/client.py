from typing import Any, Dict, Optional
from openai import OpenAI
import json


class APIClient:
    """对 OpenAI/OpenRouter 的封装"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.9,
    ) -> Optional[Dict[str, Any]]:
        """调用接口并返回结构化 JSON"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_data",
                        "strict": True,
                        "schema": response_schema,
                    },
                },
            )

            return json.loads(response.choices[0].message.content)  # type: ignore
        except Exception as e:
            print(f"API Error: {e}")
            return None
