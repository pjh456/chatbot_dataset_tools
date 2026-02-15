import respx
import json
from httpx import Response
from chatbot_dataset_tools.datasets import DatasetLoader
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.tasks.processors import LLMProcessor
from chatbot_dataset_tools.config import config, APIConfig


@respx.mock
def test_dataset_run_llm_task():
    # 1. Mock OpenAI API
    url = "https://api.openai.com/v1/chat/completions"
    mock_resp = {
        "choices": [{"message": {"content": "Enhanced Data"}}],
        "usage": {"total_tokens": 10},
    }
    respx.post(url).mock(return_value=Response(200, json=mock_resp))

    # 2. 准备数据
    ds = DatasetLoader.from_list(
        [
            Conversation([Message("user", "raw input 1")]),
            Conversation([Message("user", "raw input 2")]),
        ]
    )

    # 3. 配置 API Key (通过 switch)
    with config.switch(api=APIConfig(openai_api_key="sk-test")):
        # 4. 初始化 Processor
        processor = LLMProcessor(
            system_prompt="Enhance this", user_prompt_template="Input: ${content}"
        )

        # 5. 执行并发任务 (2线程)
        # 这会返回一个新的 Dataset
        result_ds = ds.run_task(processor, max_workers=2, ordered=True)

        # 6. 触发计算 (to_list)
        results = result_ds.to_list()

    # 7. 验证
    assert len(results) == 2
    # 验证内容被追加了
    assert results[0].messages[-1].role == "assistant"
    assert results[0].messages[-1].content == "Enhanced Data"
    # 验证 metadata 记录了 usage
    assert results[0].metadata["usage"]["total_tokens"] == 10

    # 验证请求是否正确
    assert respx.calls.call_count == 2

    # 获取所有捕获到的请求内容
    actual_prompts = []
    for call in respx.calls:
        payload = json.loads(call.request.content)
        # 提取 prompt 内容
        actual_prompts.append(payload["messages"][1]["content"])

    # 使用 set 进行无序对比，或者 sort 后对比
    expected_prompts = {"Input: raw input 1", "Input: raw input 2"}
    assert set(actual_prompts) == expected_prompts
