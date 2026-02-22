import pytest
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.datasets import InMemoryDataset, LazyDataset, ConcatDataset


@pytest.fixture
def sample_convs_1():
    return [
        Conversation([Message("user", "hello 1"), Message("assistant", "hi 1")]),
        Conversation([Message("user", "hello 2"), Message("assistant", "hi 2")]),
    ]


@pytest.fixture
def sample_convs_2():
    return [
        Conversation([Message("user", "hello 3"), Message("assistant", "hi 3")]),
    ]


def test_concat_basic_iteration(sample_convs_1, sample_convs_2):
    """测试基本串联和迭代顺序"""
    ds1 = InMemoryDataset(sample_convs_1)
    ds2 = InMemoryDataset(sample_convs_2)

    concat_ds = ConcatDataset([ds1, ds2])

    results = list(concat_ds)

    assert len(results) == 3
    assert results[0].messages[0].content == "hello 1"
    assert results[1].messages[0].content == "hello 2"
    assert results[2].messages[0].content == "hello 3"


def test_concat_with_empty_dataset(sample_convs_1):
    """测试包含空数据集的情况"""
    ds1 = InMemoryDataset(sample_convs_1)
    ds2 = InMemoryDataset([])

    concat_ds = ConcatDataset([ds1, ds2])

    results = list(concat_ds)
    assert len(results) == 2
    assert results[1].messages[0].content == "hello 2"


def test_concat_length_calculation(sample_convs_1, sample_convs_2):
    """测试长度计算"""
    ds1 = InMemoryDataset(sample_convs_1)
    ds2 = InMemoryDataset(sample_convs_2)

    concat_ds = ConcatDataset([ds1, ds2])

    assert len(concat_ds) == 3


def test_concat_length_error_with_lazy(sample_convs_1):
    """测试当包含无法预知长度的 LazyDataset 时，len() 抛出异常"""
    ds_mem = InMemoryDataset(sample_convs_1)

    # 模拟一个不知道长度的 LazyDataset
    def infinite_loader():
        while True:
            yield Conversation([Message("user", "infinite")])

    ds_lazy = LazyDataset(infinite_loader())

    concat_ds = ConcatDataset([ds_mem, ds_lazy])

    with pytest.raises(TypeError, match="unknown length"):
        _ = len(concat_ds)


def test_concat_laziness():
    """验证 ConcatDataset 保持了惰性加载特性"""
    load_count = 0

    def counter_loader():
        nonlocal load_count
        for i in range(3):
            load_count += 1
            yield Conversation([Message("user", f"msg {i}")])

    ds_lazy = LazyDataset(counter_loader())
    concat_ds = ConcatDataset([ds_lazy])

    # 初始化时 load_count 应该是 0
    assert load_count == 0

    # 迭代一个元素
    it = iter(concat_ds)
    next(it)
    assert load_count == 1

    # 再迭代一个
    next(it)
    assert load_count == 2


def test_concat_multiple_types(sample_convs_1, sample_convs_2):
    """测试混合 InMemoryDataset 和 LazyDataset"""
    ds1 = InMemoryDataset(sample_convs_1)

    def loader():
        yield from sample_convs_2

    ds2 = LazyDataset(loader())

    concat_ds = ConcatDataset([ds1, ds2])

    # 验证内容
    all_msgs = [c.messages[0].content for c in concat_ds]
    assert all_msgs == ["hello 1", "hello 2", "hello 3"]


def test_concat_map_chaining(sample_convs_1):
    """测试串联后的数据集依然可以进行 map 操作"""
    ds1 = InMemoryDataset(sample_convs_1)
    ds2 = InMemoryDataset(sample_convs_1)

    concat_ds = ConcatDataset([ds1, ds2])

    # 给所有 user 消息增加后缀
    def transform(conv):
        conv.messages[0].content += "!"
        return conv

    mapped_ds = concat_ds.map(transform)

    for conv in mapped_ds:
        assert conv.messages[0].content.endswith("!")
