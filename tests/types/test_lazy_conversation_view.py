from chatbot_dataset_tools.types import (
    Message,
    MessageList,
    LazyMessageView,
    Conversation,
)


def test_lazy_message_view():
    msgs = [
        Message("user", "hi"),
        Message("assistant", "hello"),
        Message("user", "bye"),
    ]
    ml = MessageList(msgs)

    view = LazyMessageView(ml)

    # map
    mapped = view.map(lambda m: Message(m.role, m.content.upper()))
    mapped_list = mapped.to_list()
    assert mapped_list[0].content == "HI"

    # filter
    filtered = view.filter(lambda m: m.role == "user")
    filtered_list = filtered.to_list()
    assert all(m.role == "user" for m in filtered_list)

    # __len__ / __getitem__
    assert len(filtered) == 2
    first = filtered[0]
    assert isinstance(first, Message)
    subview = filtered[0:2]
    assert isinstance(subview, LazyMessageView)
    assert len(subview) == 2

    # to_message_list / to_conversation
    ml2 = filtered.to_message_list()
    assert isinstance(ml2, MessageList)

    conv = filtered.to_conversation()
    assert isinstance(conv, Conversation)
