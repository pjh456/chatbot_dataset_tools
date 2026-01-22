import pytest
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.ops import transforms


def test_rename_roles():
    conv = Conversation([Message("human", "hi"), Message("gpt", "hello")])
    op = transforms.rename_roles({"human": "user", "gpt": "assistant"})
    new_conv = op(conv)

    assert new_conv.messages[0].role == "user"
    assert new_conv.messages[1].role == "assistant"


def test_strip_content():
    conv = Conversation([Message("user", "  hello  "), Message("assistant", "\nhi\n")])
    op = transforms.strip_content()
    new_conv = op(conv)

    assert new_conv.messages[0].content == "hello"
    assert new_conv.messages[1].content == "hi"


def test_merge_consecutive_roles():
    conv = Conversation(
        [
            Message("user", "Hello"),
            Message("user", "Are you there?"),  # 连续
            Message("assistant", "Yes"),
            Message("assistant", "I am."),  # 连续
        ]
    )
    op = transforms.merge_consecutive_roles(sep=" ")
    new_conv = op(conv)

    assert len(new_conv.messages) == 2
    assert new_conv.messages[0].role == "user"
    assert new_conv.messages[0].content == "Hello Are you there?"
    assert new_conv.messages[1].role == "assistant"
    assert new_conv.messages[1].content == "Yes I am."


def test_limit_context():
    conv = Conversation(
        [
            Message("user", "1"),
            Message("assistant", "2"),
            Message("user", "3"),
            Message("assistant", "4"),
        ]
    )
    # 只保留最后 2 条
    op = transforms.limit_context(max_messages=2)
    new_conv = op(conv)

    assert len(new_conv.messages) == 2
    assert new_conv.messages[0].content == "3"
    assert new_conv.messages[1].content == "4"


def test_remove_system_message():
    conv = Conversation(
        [
            Message("system", "sys"),
            Message("user", "hi"),
        ]
    )
    op = transforms.remove_system_message()
    new_conv = op(conv)

    assert len(new_conv.messages) == 1
    assert new_conv.messages[0].role == "user"
