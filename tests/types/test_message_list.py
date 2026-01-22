from chatbot_dataset_tools.types import Message, MessageList, Conversation


def test_message_list():

    msgs = [Message("user", "hi"), Message("assistant", "hello")]
    ml = MessageList(msgs)

    # append / extend
    ml.append(Message("user", "again"))
    assert len(ml) == 3

    ml.extend([Message("assistant", "reply1"), Message("assistant", "reply2")])
    assert len(ml) == 5

    # __getitem__ / slicing
    assert isinstance(ml[0], Message)
    sub = ml[1:3]
    assert isinstance(sub, MessageList)
    assert len(sub) == 2

    # __setitem__ / __delitem__
    ml[0] = Message("user", "modified")
    assert ml[0].content == "modified"
    del ml[0]
    assert len(ml) == 4

    # __add__ / __iadd__ / __mul__
    ml2 = ml + [Message("user", "new")]
    assert len(ml2) == len(ml) + 1
    ml += [Message("user", "another")]
    assert len(ml) == 5
    ml3 = ml * 2
    assert len(ml3) == 10

    # last / copy
    last_msg = ml.last()[0]
    assert isinstance(last_msg, Message)
    last_two = ml.last(2)
    assert isinstance(last_two, MessageList)
    ml_copy = ml.copy()
    assert all(a.content == b.content for a, b in zip(ml, ml_copy))
    assert ml_copy is not ml


test_message_list()
