import pytest
import json
from typing import Iterator
from chatbot_dataset_tools.pipeline.engine import PipelineEngine, PipelineConfig
from chatbot_dataset_tools.registry import (
    register_source,
    register_sink,
    register_transform,
    register_filter,
)
from chatbot_dataset_tools.connectors import DataSource, DataSink
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.config import config

# --- 1. 准备测试用的 Mock 组件 ---


@register_source("mock_source")
class MockSource(DataSource):
    def __init__(self, data_list, **kwargs):
        self.data = data_list

    def load(self) -> Iterator[Conversation]:
        for item in self.data:
            # 模拟从 dict 转换
            yield Conversation.from_dict(item)


# 捕获输出结果以便验证
GLOBAL_SINK_BUFFER = []


@register_sink("mock_sink")
class MockSink(DataSink):
    def __init__(self, **kwargs):
        pass

    def save(self, data) -> None:
        GLOBAL_SINK_BUFFER.clear()
        for item in data:
            GLOBAL_SINK_BUFFER.append(item)


@register_transform("test_append")
def append_suffix(suffix: str):
    def _op(conv: Conversation) -> Conversation:
        for m in conv.messages:
            m.content += suffix
        return conv

    return _op


@register_filter("test_filter_user")
def filter_by_user(name: str):
    return lambda c: c.messages[0].role == name


# --- 2. 真正的集成测试 ---


def test_full_pipeline_flow(tmp_path):
    """
    测试完整流程：
    JSON Config -> Engine -> Loader(Mock) -> Map -> Filter -> Context Override -> Saver(Mock)
    """

    # 1. 准备 Mock 数据
    raw_data = [
        {"messages": [{"role": "user", "content": "A"}]},
        {"messages": [{"role": "system", "content": "Ignore me"}]},  # 将被过滤
        {"messages": [{"role": "user", "content": "B"}]},
    ]

    # 2. 构建 Pipeline 配置 (Dictionary 模拟 JSON)
    pipeline_json = {
        "name": "Integration Test Pipeline",
        "settings": {"proc": {"max_workers": 99}},  # 测试配置覆盖
        "steps": [
            {
                "name": "Load Mock Data",
                "type": "loader",
                "params": {
                    "inputs": [{"source_type": "mock_source", "data_list": raw_data}]
                },
            },
            {
                "name": "Filter Only User Starts",
                "type": "filter",
                "params": {"op": "test_filter_user", "name": "user"},
            },
            {
                "name": "Append Suffix",
                "type": "map",
                "params": {"op": "test_append", "suffix": "_checked"},
            },
            {
                "name": "Save to Buffer",
                "type": "saver",
                "params": {"sink_type": "mock_sink"},
            },
        ],
    }

    # 保存为临时文件以测试 from_file
    config_file = tmp_path / "pipeline.json"
    with open(config_file, "w") as f:
        json.dump(pipeline_json, f)

    # 3. 初始化并运行 Engine
    engine = PipelineEngine(str(config_file))

    # 在运行前，确保全局配置不是 99
    assert config.settings.proc.max_workers != 99

    engine.run()

    # 4. 验证结果

    # 过滤后应该只剩 2 条 (system 那条被丢弃)
    assert len(GLOBAL_SINK_BUFFER) == 2

    # 验证 Map 效果
    assert GLOBAL_SINK_BUFFER[0].messages[0].content == "A_checked"
    assert GLOBAL_SINK_BUFFER[1].messages[0].content == "B_checked"

    # 验证上下文是否恢复 (测试 config.switch)
    assert config.settings.proc.max_workers != 99


def test_pipeline_with_concat_files(tmp_path):
    """测试真实文件读写和 Concat"""

    # 1. 创建两个真实的 jsonl 文件
    f1 = tmp_path / "part1.jsonl"
    f2 = tmp_path / "part2.jsonl"
    out = tmp_path / "merged.jsonl"

    with open(f1, "w") as f:
        f.write('{"messages": [{"role": "user", "content": "1"}]}\n')
    with open(f2, "w") as f:
        f.write('{"messages": [{"role": "user", "content": "2"}]}\n')

    # 2. 配置
    pipeline_conf = {
        "name": "File IO Test",
        "steps": [
            {
                "type": "loader",
                "params": {
                    "inputs": [
                        {
                            "source_type": "FileSource",
                            "path": str(f1),
                            "format": "jsonl",
                        },
                        {
                            "source_type": "FileSource",
                            "path": str(f2),
                            "format": "jsonl",
                        },
                    ]
                },
            },
            {
                "type": "saver",
                "params": {
                    "sink_type": "FileSink",
                    "path": str(out),
                    "format": "jsonl",
                },
            },
        ],
    }

    cfg = PipelineConfig.from_dict(pipeline_conf)
    engine = PipelineEngine(cfg)
    engine.run()

    # 3. 验证输出文件
    assert out.exists()
    with open(out, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert "1" in lines[0]
        assert "2" in lines[1]
