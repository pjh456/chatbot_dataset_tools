import pytest
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.formatters import (
    ShareGPTFormatter,
    AlpacaFormatter,
    OpenAIFormatter,
)

# ---------------------------------------------------------
# 1. ShareGPT & OpenAI: 来回一致性测试 (Round-trip)
# ---------------------------------------------------------


@pytest.mark.parametrize("formatter_class", [ShareGPTFormatter, OpenAIFormatter])
def test_standard_roundtrip(formatter_class):
    """测试标准多轮格式在转换后能原样解析回来"""
    formatter = formatter_class()

    # 构造原始对话，包含 metadata
    original_conv = Conversation(
        data=[
            Message("system", "You are an assistant."),
            Message("user", "Hello!"),
            Message("assistant", "Hi, how can I help?"),
        ],
        meta={"id": "test_001", "source": "unit_test"},
    )

    # 执行转换: Conv -> Dict
    data = formatter.format(original_conv)

    # 验证生成的字典结构 (简单抽查)
    if formatter_class == ShareGPTFormatter:
        assert "conversations" in data
        assert data["conversations"][0]["from"] == "system"
        assert data["conversations"][1]["from"] == "human"  # 验证角色映射
    else:  # OpenAI
        assert "messages" in data
        assert data["messages"][1]["role"] == "user"

    # 执行解析: Dict -> Conv
    parsed_conv = formatter.parse(data)

    # 验证消息内容一致性
    assert len(parsed_conv.messages) == len(original_conv.messages)
    for i in range(len(original_conv.messages)):
        assert parsed_conv.messages[i].role == original_conv.messages[i].role
        assert parsed_conv.messages[i].content == original_conv.messages[i].content

    # 验证元数据一致性 (OpenAI 目前实现未处理 metadata，ShareGPT 处理了)
    if formatter_class == ShareGPTFormatter:
        assert parsed_conv.metadata["id"] == "test_001"


# ---------------------------------------------------------
# 2. Alpaca: 专用映射逻辑测试
# ---------------------------------------------------------


def test_alpaca_format_logic():
    formatter = AlpacaFormatter()

    # 场景 A: 带 System 的单轮
    conv_a = Conversation(
        [
            Message("system", "Be concise"),
            Message("user", "Who are you?"),
            Message("assistant", "I am an AI."),
        ]
    )
    data_a = formatter.format(conv_a)
    assert data_a["instruction"] == "Be concise"
    assert data_a["input"] == "Who are you?"
    assert data_a["output"] == "I am an AI."

    # 场景 B: 不带 System 的单轮 (User 应该被挤到 instruction 里)
    conv_b = Conversation(
        [Message("user", "Pure question"), Message("assistant", "Pure answer")]
    )
    data_b = formatter.format(conv_b)
    assert data_b["instruction"] == "Pure question"
    assert data_b["input"] == ""
    assert data_b["output"] == "Pure answer"


def test_alpaca_parse_logic():
    formatter = AlpacaFormatter()

    # 模拟外部读入的 Alpaca 字典
    raw_data = {
        "instruction": "Summarize",
        "input": "Long text...",
        "output": "Summary.",
    }

    conv = formatter.parse(raw_data)
    assert len(conv.messages) == 3
    assert conv.messages[0].role == "system"
    assert conv.messages[0].content == "Summarize"
    assert conv.messages[1].role == "user"
    assert conv.messages[2].role == "assistant"


# ---------------------------------------------------------
# 3. 边界情况测试
# ---------------------------------------------------------


def test_formatter_empty_data():
    """测试空对话是否会崩溃"""
    empty_conv = Conversation([])

    for fmt in [ShareGPTFormatter(), OpenAIFormatter(), AlpacaFormatter()]:
        data = fmt.format(empty_conv)
        assert isinstance(data, dict)

        parsed = fmt.parse(data)
        assert len(parsed.messages) == 0


def test_sharegpt_custom_roles():
    """测试 ShareGPT 处理非标准角色的表现"""
    formatter = ShareGPTFormatter()
    conv = Conversation(
        [
            Message("observation", "The weather is sunny"),  # 非标准角色
        ]
    )

    data = formatter.format(conv)
    # 角色名应保持原样
    assert data["conversations"][0]["from"] == "observation"

    parsed = formatter.parse(data)
    assert parsed.messages[0].role == "observation"
