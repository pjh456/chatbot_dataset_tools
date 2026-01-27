from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.datasets import InMemoryDataset
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.ops.transforms import rename_roles


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


def test_in_memory_context_propagation():
    """测试 InMemoryDataset 在 map 时正确应用绑定的配置"""
    # 1. 创建数据集，并绑定一个特殊的 role_map
    custom_ctx = config.current.clone(ds={"role_map": {"user": "client"}})
    convs = [Conversation([Message("user", "hello")])]
    ds = InMemoryDataset(convs, ctx=custom_ctx)

    # 2. 使用一个依赖全局配置的 transform (不传参数，让它去读配置)
    # rename_roles 内部会调用 config.settings.ds.role_map
    renamed_ds = ds.map(rename_roles())

    # 3. 验证结果是否使用了 "client" 而不是默认的 "human"
    assert renamed_ds.to_list()[0].messages[0].role == "client"


def test_in_memory_filter_context():
    """测试 filter 过程中的上下文切换"""
    from chatbot_dataset_tools.ops.filters import is_valid_alternating

    # 设置一个非标准的系统角色名
    custom_ctx = config.current.clone(ds={"role_map": {"system": "instruction"}})
    convs = [Conversation([Message("instruction", "be nice"), Message("user", "hi")])]
    ds = InMemoryDataset(convs, ctx=custom_ctx)

    # is_valid_alternating 内部会查找系统消息并过滤它
    # 如果它读不到 "instruction" 是系统角色，校验就会失败
    assert len(ds.filter(is_valid_alternating())) == 1
