import json
import pytest
from pathlib import Path
from typing import Mapping, Any
from chatbot_dataset_tools.connectors import FileSource, FileSink
from chatbot_dataset_tools.config import config, FileConfig
from chatbot_dataset_tools.types import Conversation, Message

# --- Fixtures ---


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
def temp_json_file(tmp_path, sample_conversations):
    """创建一个临时的 JSON 数据文件"""
    path = tmp_path / "test_data.json"
    data = [c.to_dict() for c in sample_conversations]
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def temp_jsonl_file(tmp_path, sample_conversations):
    """创建一个临时的 JSONL 数据文件"""
    path = tmp_path / "test_data.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for c in sample_conversations:
            f.write(json.dumps(c.to_dict()) + "\n")
    return path


# --- Test FileSource ---


class TestFileSource:
    def test_load_json(self, temp_json_file, sample_conversations):
        cfg = FileConfig(path=temp_json_file, format="json")
        source = FileSource(file_cfg=cfg)

        results = list(source.load())

        assert len(results) == 2
        assert results[0].messages[0].content == "Hello"
        assert results[1].metadata["id"] == "002"

    def test_load_jsonl(self, temp_jsonl_file, sample_conversations):
        cfg = FileConfig(path=temp_jsonl_file, format="jsonl")
        source = FileSource(file_cfg=cfg)

        results = list(source.load())

        assert len(results) == 2
        assert results[0].messages[1].role == "assistant"

    def test_unsupported_format(self, tmp_path):
        cfg = FileConfig(path=tmp_path / "test.txt", format="xml")
        source = FileSource(file_cfg=cfg)

        with pytest.raises(NotImplementedError, match="does not support format: 'xml'"):
            results = list(source.load())

    def test_invalid_json_structure(self, tmp_path):
        # JSON 不是列表，FileSource._load_json 应该报错
        path = tmp_path / "wrong.json"
        path.write_text(json.dumps({"not": "a list"}))

        source = FileSource(file_cfg=FileConfig(path=path, format="json"))
        with pytest.raises(ValueError, match="Json Data Must be a list"):
            results = list(source.load())


# --- Test FileSink ---


class TestFileSink:
    def test_save_json(self, tmp_path, sample_conversations):
        target_path = tmp_path / "output.json"
        cfg = FileConfig(path=target_path, format="json", indent=4)
        sink = FileSink(file_cfg=cfg)

        sink.save(sample_conversations)

        # 验证文件是否存在并解析内容
        assert target_path.exists()
        with open(target_path, "r") as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]["messages"][0]["content"] == "Hello"

    def test_save_jsonl(self, tmp_path, sample_conversations):
        target_path = tmp_path / "output.jsonl"
        cfg = FileConfig(path=target_path, format="jsonl")
        sink = FileSink(file_cfg=cfg)

        sink.save(sample_conversations)

        # 验证 JSONL 格式（每行一个 JSON）
        lines = target_path.read_text().strip().split("\n")
        assert len(lines) == 2
        first_line = json.loads(lines[0])
        assert first_line["messages"][0]["content"] == "Hello"


# --- Test Config Integration ---


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


# --- Test Custom Conversation Type (Generic T) ---


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
