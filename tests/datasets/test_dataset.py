import pytest
from chatbot_dataset_tools.datasets import Dataset, DatasetLoader
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.ops.filters import min_turns
from chatbot_dataset_tools.ops.transforms import rename_roles
import pytest


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
    filtered = ds.filter(min_turns(2))
    assert len(filtered.to_list()) == 2

    # 2. 测试 rename_roles
    renamed = ds.map(rename_roles({"human": "user", "gpt": "assistant"}))
    items = renamed.to_list()
    assert items[2].messages[0].role == "user"
    assert items[2].messages[1].role == "assistant"

    # 3. 测试 limit
    limited = ds.limit(2)
    assert len(limited.to_list()) == 2

    # 4. 测试链式调用组合
    final_ds = (
        ds.filter(min_turns(2))
        .map(rename_roles({"human": "user", "gpt": "assistant"}))
        .limit(1)
    )
    result = final_ds.to_list()
    assert len(result) == 1
    assert result[0].messages[0].content == "hi"


@pytest.fixture
def large_dataset():
    """创建一个包含 10 条数据的测试集"""
    convs = [Conversation([Message("user", f"msg {i}")]) for i in range(10)]
    return DatasetLoader.from_list(convs)


def test_dataset_split(large_dataset):
    # 测试 8/2 分成两个数据集
    train_ds, val_ds = large_dataset.split(0.8)

    assert len(train_ds) == 8
    assert len(val_ds) == 2

    # 验证内容是否连续（默认 split 通常是不打乱的）
    assert train_ds.to_list()[0].messages[0].content == "msg 0"
    assert val_ds.to_list()[0].messages[0].content == "msg 8"


def test_dataset_shuffle(large_dataset):
    # 使用固定种子进行打乱
    shuffled_1 = large_dataset.shuffle(seed=42)
    shuffled_2 = large_dataset.shuffle(seed=42)
    shuffled_different = large_dataset.shuffle(seed=99)

    # 1. 验证长度不变
    assert len(shuffled_1) == len(large_dataset)

    # 2. 验证相同种子结果一致（幂等性）
    list1 = [c.messages[0].content for c in shuffled_1]
    list2 = [c.messages[0].content for c in shuffled_2]
    assert list1 == list2

    # 3. 验证不同种子结果不同（大概率）
    list3 = [c.messages[0].content for c in shuffled_different]
    assert list1 != list3

    # 4. 验证集合内容是一致的（没有丢数据或产生幻觉）
    assert set(list1) == set(f"msg {i}" for i in range(10))


def test_dataset_sample(large_dataset):
    # 采样 3 条
    sampled = large_dataset.sample(n=3, seed=123)

    assert len(sampled) == 3
    # 验证采样出的数据确实属于原数据集
    all_contents = [c.messages[0].content for c in large_dataset]
    for c in sampled:
        assert c.messages[0].content in all_contents


def test_dataset_sample_overflow(large_dataset):
    # 如果采样数大于总数，应该返回全部数据而不是报错
    sampled = large_dataset.sample(n=100)
    assert len(sampled) == 10
