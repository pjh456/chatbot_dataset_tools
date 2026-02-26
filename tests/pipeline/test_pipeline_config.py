import pytest
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.config import config


@pytest.fixture
def sample_messages():
    return [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there"),
    ]


@pytest.fixture
def sample_conversation(sample_messages):
    return Conversation(data=sample_messages, meta={"id": "123"})


@pytest.fixture(autouse=True)
def reset_config():
    """每个测试运行前重置全局配置，避免污染"""
    original_settings = config.settings
    yield
    # 这里因为 config 是单例，简单的重置方法可以是重新赋值，
    # 或者依赖 ConfigContext 的 switch 机制自动还原。
    # 在本测试中，主要依赖 Context 的自动还原。
    pass
