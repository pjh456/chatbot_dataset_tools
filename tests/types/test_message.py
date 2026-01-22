from chatbot_dataset_tools.types import Message


def test_message():
    # 构造与属性
    m = Message(role="user", content="Hello")
    assert m.role == "user"
    assert m.content == "Hello"
    assert isinstance(m.metadata, dict)

    # __str__ / __repr__
    assert str(m) == "[user] Hello"
    assert repr(m) == "Message(role='user', content='Hello', metadata={})"

    # copy 不绑定原容器
    m2 = m.copy()
    assert m2.role == m.role
    assert m2.content == m.content
    assert m2 is not m


test_message()
