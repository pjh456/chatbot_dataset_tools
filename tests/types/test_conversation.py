from chatbot_dataset_tools.types import (
    Message,
    MessageList,
    LazyMessageView,
    Conversation,
)


def test_conversation():
    msgs = [Message("user", "hi"), Message("assistant", "hello")]
    conv = Conversation(msgs)

    # messages 属性
    ml = conv.messages
    assert isinstance(ml, MessageList)
    assert len(ml) == 2

    # view
    view = conv.view()
    assert isinstance(view, LazyMessageView)
    assert len(view) == 2

    # __str__ / __repr__
    assert "<Conversation" in str(conv)
    assert "Conversation(" in repr(conv)
