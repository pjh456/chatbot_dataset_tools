from chatbot_dataset_tools.tasks.processor import BaseProcessor
from chatbot_dataset_tools.types import Message, Conversation


class UpperCaseProcessor(BaseProcessor):
    """简单的算子：将内容全部转为大写"""

    def process(self, conv: Conversation) -> Conversation:
        for m in conv.messages:
            m.content = m.content.upper()
        return conv


class FilterProcessor(BaseProcessor):
    """带过滤逻辑的算子：如果内容包含 'skip' 则返回 None"""

    def process(self, conv: Conversation) -> Conversation | None:
        if "skip" in conv.messages[0].content:
            return None
        return conv


def test_processor_basic():
    processor = UpperCaseProcessor()
    conv = Conversation([Message("user", "hello")])
    result = processor.process(conv)
    assert result.messages[0].content == "HELLO"


def test_processor_filter():
    processor = FilterProcessor()
    conv_keep = Conversation([Message("user", "keep me")])
    conv_skip = Conversation([Message("user", "skip me")])

    assert processor.process(conv_keep) is not None
    assert processor.process(conv_skip) is None
