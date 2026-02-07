import json
import pytest
from pathlib import Path
from typing import Mapping, Any
from chatbot_dataset_tools.config import config, FileConfig
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.connectors import FileSource, FileSink


@pytest.fixture
def sample_conversations():
    """提供一组用于测试的 Conversation 对象"""
    conv1 = Conversation(
        [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ],
        meta={"id": "001"},
    )

    conv2 = Conversation(
        [
            Message(role="user", content="How is the weather?"),
            Message(role="assistant", content="Sunny."),
        ],
        meta={"id": "002"},
    )

    return [conv1, conv2]


@pytest.fixture
def temp_jsonl_file(tmp_path, sample_conversations):
    """创建一个临时的 JSONL 数据文件"""
    path = tmp_path / "test_data.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for c in sample_conversations:
            f.write(json.dumps(c.to_dict()) + "\n")
    return path


class TestConnectorsWithConfig:
    def test_source_uses_global_config(self, temp_jsonl_file):
        """测试如果不传 file_cfg，Source 是否从 config.current 读取"""
        with config.switch(path=str(temp_jsonl_file), format="jsonl"):
            source = FileSource()
            assert source.path == str(temp_jsonl_file)
            assert source.format == "jsonl"

            results = list(source.load())
            assert len(results) == 2

    def test_sink_uses_global_config(self, tmp_path, sample_conversations):
        """测试 Sink 是否响应全局配置切换"""
        out_path = tmp_path / "global_test.jsonl"

        with config.switch(path=str(out_path), format="jsonl"):
            sink = FileSink()
            sink.save(sample_conversations)

        assert out_path.exists()
        assert len(out_path.read_text().strip().split("\n")) == 2


def test_custom_conv_type(tmp_path):
    """测试通过 conv_type 参数传递自定义类"""

    class CustomConv(Conversation):
        def __init__(self, content: str):
            # 调用父类初始化或按需实现
            super().__init__()
            self.content = content

        @classmethod
        def from_dict(cls, data: Mapping[str, Any]) -> "CustomConv":  # type: ignore
            # 实现逻辑
            content = data["messages"][0]["content"]
            return cls(content)

    path = tmp_path / "custom.jsonl"
    path.write_text(json.dumps({"messages": [{"role": "u", "content": "special"}]}))

    source = FileSource(
        file_cfg=FileConfig(path=path, format="jsonl"), conv_type=CustomConv
    )

    results = list(source.load())
    assert isinstance(results[0], CustomConv)
    assert results[0].content == "special"
