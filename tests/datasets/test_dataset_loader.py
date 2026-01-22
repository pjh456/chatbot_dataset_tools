import json
import tempfile
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.datasets import DatasetLoader


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
