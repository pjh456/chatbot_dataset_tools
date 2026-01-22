import pytest
from chatbot_dataset_tools.datasets import Dataset, DatasetLoader
from chatbot_dataset_tools.types import Message, Conversation


def test_dataset_base_class():
    class DummyDataset(Dataset):
        pass

    dataset = DummyDataset()

    with pytest.raises(NotImplementedError):
        list(dataset)

    with pytest.raises(NotImplementedError):
        len(dataset)


def test_dataset_fluent_api():
    # 构造测试数据
    c1 = Conversation([Message("user", "hi"), Message("bot", "hello")])  # 2 turns
    c2 = Conversation([Message("user", "bye")])  # 1 turn
    c3 = Conversation(
        [Message("human", "how are you"), Message("gpt", "fine")]
    )  # 2 turns

    ds = DatasetLoader.from_list([c1, c2, c3])

    # 1. 测试 filter_turns
    filtered = ds.filter_turns(min_turns=2)
    assert len(filtered.to_list()) == 2

    # 2. 测试 rename_roles
    renamed = ds.rename_roles({"human": "user", "gpt": "assistant"})
    items = renamed.to_list()
    assert items[2].messages[0].role == "user"
    assert items[2].messages[1].role == "assistant"

    # 3. 测试 limit
    limited = ds.limit(2)
    assert len(limited.to_list()) == 2

    # 4. 测试链式调用组合
    final_ds = (
        ds.filter_turns(min_turns=2)
        .rename_roles({"human": "user", "gpt": "assistant"})
        .limit(1)
    )
    result = final_ds.to_list()
    assert len(result) == 1
    assert result[0].messages[0].content == "hi"
