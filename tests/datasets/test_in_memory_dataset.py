from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.datasets import InMemoryDataset


def test_in_memory_dataset():
    convs = [
        Conversation([Message("user", "Hello"), Message("assistant", "Hi")]),
        Conversation([Message("user", "How are you?"), Message("assistant", "Good")]),
        Conversation([Message("user", "Bye"), Message("assistant", "See you")]),
    ]

    mem_ds = InMemoryDataset(convs)
    assert len(mem_ds) == 3
    items = list(mem_ds)
    assert all(isinstance(c, Conversation) for c in items)

    # map 测试
    upper_ds = mem_ds.map(
        lambda c: Conversation([Message(m.role, m.content.upper()) for m in c.messages])
    )
    for orig, mapped in zip(mem_ds, upper_ds):
        for m1, m2 in zip(orig.messages, mapped.messages):
            assert m2.content == m1.content.upper()

    # filter 测试
    filtered_ds = mem_ds.filter(lambda c: any(m.content == "Hello" for m in c.messages))
    assert len(list(filtered_ds)) == 1
    assert list(filtered_ds)[0].messages[0].content == "Hello"
