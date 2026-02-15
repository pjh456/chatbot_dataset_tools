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


def test_conversation_uid_from_metadata():
    """测试显式 ID 优先级最高"""
    conv = Conversation([Message("user", "hi")], meta={"id": "custom-123"})
    assert conv.get_uid() == "custom-123"


def test_conversation_uid_deterministic_hash():
    """测试无 ID 时，相同内容生成相同哈希，不同内容生成不同哈希"""
    c1 = Conversation([Message("user", "hello"), Message("assistant", "hi")])
    c2 = Conversation([Message("user", "hello"), Message("assistant", "hi")])
    c3 = Conversation([Message("user", "hello"), Message("assistant", "different")])

    # 确定性：相同内容结果一致
    uid1 = c1.get_uid()
    uid2 = c2.get_uid()
    assert uid1 == uid2
    assert len(uid1) == 64  # SHA-256 长度

    # 区分性：不同内容结果不同
    assert uid1 != c3.get_uid()


def test_conversation_uid_ignores_metadata_changes():
    """测试修改无关的 metadata 不会改变基于内容的 UID"""
    conv = Conversation([Message("user", "hello")])
    initial_uid = conv.get_uid()

    conv.metadata["source"] = "web"
    # 注意：如果之前已经缓存了 UID，且没手动清理，它应该保持不变
    assert conv.get_uid() == initial_uid


def test_conversation_set_usage():
    """测试 Conversation 对象是否可以在 set 中去重"""
    c1 = Conversation([Message("user", "a")])
    c2 = Conversation([Message("user", "a")])  # 内容相同
    c3 = Conversation([Message("user", "b")])

    s = {c1, c2, c3}
    assert len(s) == 2  # c1 和 c2 应该被视为同一个
