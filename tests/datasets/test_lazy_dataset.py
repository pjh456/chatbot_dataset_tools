from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.datasets import LazyDataset
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.ops.transforms import rename_roles


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


def test_lazy_dataset_context_switching():
    """测试 LazyDataset 在迭代时自动切换上下文"""
    # 1. 创建一个绑定了特殊配置的 LazyDataset
    # user 被映射为 'customer'
    ctx = config.current.clone(ds={"role_map": {"user": "customer"}})
    raw_data = [Conversation([Message("user", "hello")])]

    # 绑定 rename_roles transform，但不传 mapping 参数
    lazy_ds = LazyDataset(raw_data, ctx=ctx).map(rename_roles())

    # 2. 在外部修改全局配置（故意干扰）
    with config.switch(ds={"role_map": {"user": "alien"}}):
        # 3. 执行迭代
        results = list(lazy_ds)

        # 验证：结果应该是 'customer' 而不是 'alien'
        # 证明 LazyDataset 在迭代内部成功 switch 到了自己的 ctx
        assert results[0].messages[0].role == "customer"


def test_lazy_dataset_chain_inheritance():
    """测试链式操作后的上下文继承"""
    ctx = config.current.clone(name="my-app-ctx")
    ds = LazyDataset([], ctx=ctx)

    # 经过多次变换
    ds2 = ds.map(lambda x: x).filter(lambda x: True)

    # 验证上下文 ID 一致
    assert ds2.ctx.uid == ctx.uid
    assert ds2.ctx.name == "my-app-ctx"
