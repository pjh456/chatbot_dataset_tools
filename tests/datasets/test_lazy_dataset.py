from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.datasets import LazyDataset


def test_lazy_dataset():
    convs = [
        Conversation([Message("user", "Hello"), Message("assistant", "Hi")]),
        Conversation([Message("user", "How are you?"), Message("assistant", "Good")]),
        Conversation([Message("user", "Bye"), Message("assistant", "See you")]),
    ]
    # ---- LazyDataset ----
    lazy_ds = LazyDataset(convs)

    # 链式 map/filter
    lazy_ds2 = lazy_ds.map(
        lambda c: Conversation([Message(m.role, m.content.upper()) for m in c.messages])
    ).filter(lambda c: any("HELLO" in m.content for m in c.messages))

    results = list(lazy_ds2)
    assert len(results) == 1
    for m in results[0].messages:
        assert m.content.isupper()

    # batch 测试
    batches = list(lazy_ds.batch(2))
    assert len(batches) == 2  # 3 对话 -> 2 批
    assert len(batches[0]) == 2
    assert len(batches[1]) == 1
