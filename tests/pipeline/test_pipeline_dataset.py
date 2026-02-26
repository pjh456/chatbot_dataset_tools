from chatbot_dataset_tools.datasets import InMemoryDataset, ConcatDataset
from chatbot_dataset_tools.types import Conversation, Message


def test_concat_dataset():
    """测试多数据集拼接"""
    data1 = [Conversation([Message("user", "1")])]
    data2 = [Conversation([Message("user", "2")])]
    data3 = [Conversation([Message("user", "3")])]

    ds1 = InMemoryDataset(data1)
    ds2 = InMemoryDataset(data2)
    ds3 = InMemoryDataset(data3)

    # 拼接
    concat_ds = ConcatDataset([ds1, ds2, ds3])

    # 验证长度
    assert len(concat_ds) == 3

    # 验证内容顺序
    items = list(concat_ds)
    assert items[0].messages[0].content == "1"
    assert items[1].messages[0].content == "2"
    assert items[2].messages[0].content == "3"


def test_concat_dataset_empty():
    """测试包含空数据集的情况"""
    ds1 = InMemoryDataset([Conversation([Message("user", "1")])])
    ds_empty = InMemoryDataset([])

    concat = ConcatDataset([ds1, ds_empty])
    assert len(concat) == 1
    assert list(concat)[0].messages[0].content == "1"
