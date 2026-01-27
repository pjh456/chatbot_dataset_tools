import pytest
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.formatters import (
    ShareGPTFormatter,
    AlpacaFormatter,
    OpenAIFormatter,
)
from chatbot_dataset_tools.config import config

# 定义测试用的标准映射
TEST_ROLE_MAP = {"user": "human", "assistant": "gpt", "system": "system"}


@pytest.mark.parametrize("formatter_class", [ShareGPTFormatter, OpenAIFormatter])
def test_standard_roundtrip(formatter_class):
    """测试在指定配置下的来回转换"""

    # 使用 switch 动态注入测试环境需要的角色映射
    with config.switch(ds={"role_map": TEST_ROLE_MAP}):
        formatter = formatter_class()  # 自动获取 TEST_ROLE_MAP

        original_conv = Conversation(
            data=[
                Message("system", "You are an assistant."),
                Message("user", "Hello!"),
                Message("assistant", "Hi, how can I help?"),
            ],
            meta={"id": "test_001"},
        )

        # 1. Format
        data = formatter.format(original_conv)

        # 验证 ShareGPT 是否正确使用了配置中的 'human'
        if formatter_class == ShareGPTFormatter:
            assert data["conversations"][1]["from"] == "human"

        # 2. Parse
        parsed_conv = formatter.parse(data)

        # 3. Assert
        assert len(parsed_conv.messages) == len(original_conv.messages)
        for i in range(len(original_conv.messages)):
            assert parsed_conv.messages[i].role == original_conv.messages[i].role
            assert parsed_conv.messages[i].content == original_conv.messages[i].content


def test_alpaca_with_custom_config():
    """测试 Alpaca 是否遵循配置中的角色定义来识别消息"""
    # 假设用户定义 'assistant' 的别名是 'bot'
    custom_map = {"user": "user", "assistant": "bot", "system": "system"}

    with config.switch(ds={"role_map": custom_map}):
        formatter = AlpacaFormatter()
        conv = Conversation([Message("user", "1+1?"), Message("assistant", "2")])

        data = formatter.format(conv)
        # 虽然 Alpaca 的 key 是固定的 instruction/output，
        # 但它内部通过 role_map 判定谁是 assistant
        assert data["output"] == "2"


def test_formatter_instance_isolation():
    """测试两个 Formatter 实例是否可以持有不同的 role_map 而互不干扰"""
    fmt_a = ShareGPTFormatter(role_map={"user": "A_User"})
    fmt_b = ShareGPTFormatter(role_map={"user": "B_User"})

    conv = Conversation([Message("user", "hi")])

    assert fmt_a.format(conv)["conversations"][0]["from"] == "A_User"
    assert fmt_b.format(conv)["conversations"][0]["from"] == "B_User"
