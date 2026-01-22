import json
import tempfile
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.datasets import DatasetLoader
from pathlib import Path
from chatbot_dataset_tools.ops.transforms import rename_roles


def test_dataset_loader():
    # 构造临时 JSON 文件
    data = [
        [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}],
        [
            {"role": "user", "content": "Bye"},
            {"role": "assistant", "content": "See you"},
        ],
    ]

    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        tmp_path = f.name

    dataset = DatasetLoader.from_json(tmp_path)
    items = list(dataset)
    assert len(items) == 2
    assert all(isinstance(c, Conversation) for c in items)
    assert items[0].messages[0].content == "Hi"
    assert items[1].messages[1].content == "See you"

    # map 测试
    upper_dataset = dataset.map(
        lambda c: Conversation([Message(m.role, m.content.upper()) for m in c.messages])
    )
    for c in upper_dataset:
        for m in c.messages:
            assert m.content.isupper()


def test_dataset_jsonl_io():
    # 1. 准备数据
    raw_data = [
        {"messages": [{"role": "user", "content": "hello"}], "metadata": {"id": 1}},
        {"messages": [{"role": "user", "content": "world"}], "metadata": {"id": 2}},
    ]

    # 创建随机的输入文件路径
    with tempfile.NamedTemporaryFile(
        "w+", delete=False, suffix="_in.jsonl", encoding="utf-8"
    ) as f_in:
        for entry in raw_data:
            f_in.write(json.dumps(entry) + "\n")
        tmp_in_path = f_in.name

    # 创建随机的输出文件路径
    # delete=False 是为了让这个文件在 close 之后依然存在，方便后面 Dataset 写入
    with tempfile.NamedTemporaryFile(delete=False, suffix="_out.jsonl") as f_out:
        tmp_out_path = f_out.name

    out_path = Path(tmp_out_path)
    in_path = Path(tmp_in_path)

    try:
        # 2. 测试从 JSONL 加载
        ds = DatasetLoader.from_jsonl(in_path)

        # 第一次遍历：验证读取内容
        items = ds.to_list()
        assert len(items) == 2
        assert items[0].messages[0].content == "hello"
        assert items[1].metadata["id"] == 2

        # 3. 测试写入 JSONL (第二次遍历)
        # 这一步会触发 Dataset 重新打开文件流
        ds.map(rename_roles({"user": "human"})).to_jsonl(out_path)

        # 4. 验证写入的文件内容
        assert out_path.exists()
        with open(out_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2
            first_line = json.loads(lines[0])
            # 验证 rename_roles 是否生效
            assert first_line["messages"][0]["role"] == "human"

    finally:
        # 5. 最后统一清理所有临时文件
        if in_path.exists():
            in_path.unlink()
        if out_path.exists():
            out_path.unlink()


def test_loader_from_list():
    c = Conversation([Message("user", "test")])
    ds = DatasetLoader.from_list([c])
    assert len(ds) == 1
    assert isinstance(ds.to_list()[0], Conversation)
