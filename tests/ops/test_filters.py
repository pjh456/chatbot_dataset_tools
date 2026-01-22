import pytest
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.ops import filters


@pytest.fixture
def sample_conv():
    return Conversation(
        [
            Message("system", "You are a bot"),
            Message("user", "Hello"),
            Message("assistant", "Hi there!"),
        ]
    )


def test_min_turns(sample_conv):
    assert filters.min_turns(3)(sample_conv) is True
    assert filters.min_turns(4)(sample_conv) is False


def test_has_role(sample_conv):
    assert filters.has_role("system")(sample_conv) is True
    assert filters.has_role("other")(sample_conv) is False


def test_content_contains(sample_conv):
    # 测试包含
    assert filters.content_contains("Hello")(sample_conv) is True
    # 测试大小写不敏感
    assert filters.content_contains("hello", case_sensitive=False)(sample_conv) is True
    # 测试大小写敏感
    assert filters.content_contains("hello", case_sensitive=True)(sample_conv) is False
    # 测试不存在
    assert filters.content_contains("Goodbye")(sample_conv) is False


def test_is_valid_alternating():
    valid = Conversation(
        [Message("user", "1"), Message("assistant", "2"), Message("user", "3")]
    )
    invalid = Conversation(
        [
            Message("user", "1"),
            Message("user", "2"),  # 连续两个 user
            Message("assistant", "3"),
        ]
    )
    assert filters.is_valid_alternating()(valid) is True
    assert filters.is_valid_alternating()(invalid) is False
