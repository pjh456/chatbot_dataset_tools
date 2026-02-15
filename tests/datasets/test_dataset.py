import pytest
import time
import json
import tempfile
from pathlib import Path
from chatbot_dataset_tools.datasets import DatasetLoader
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.tasks.processors import BaseProcessor


class SlowProcessor(BaseProcessor):
    """模拟耗时任务，用于测试并发和顺序"""

    def process(self, conv: Conversation) -> Conversation:
        # 如果内容是 "slow"，睡久一点
        if "slow" in conv.messages[0].content:
            time.sleep(0.2)
        return conv


class ErrorProcessor(BaseProcessor):
    """模拟报错任务"""

    def process(self, conv: Conversation) -> Conversation:
        raise ValueError("Intentional Error")


def test_run_task_basic_and_ordered():
    """测试基础任务执行和顺序保持"""
    c1 = Conversation([Message("user", "slow msg")])  # 会睡 0.2s
    c2 = Conversation([Message("user", "fast msg")])
    ds = DatasetLoader.from_list([c1, c2])

    # 测试 ordered=True (默认)
    # 虽然 c1 慢，但结果列表里 c1 必须在 c2 前面
    results_ordered = ds.run_task(
        SlowProcessor(), max_workers=2, ordered=True
    ).to_list()
    assert results_ordered[0].messages[0].content == "slow msg"
    assert results_ordered[1].messages[0].content == "fast msg"


def test_run_task_unordered():
    """测试乱序执行 (谁快谁先出)"""
    c1 = Conversation([Message("user", "slow msg")])
    c2 = Conversation([Message("user", "fast msg")])
    ds = DatasetLoader.from_list([c1, c2])

    # 测试 ordered=False
    # c2 快，在并发下 c2 应该先出现在结果里
    results_unordered = ds.run_task(
        SlowProcessor(), max_workers=2, ordered=False
    ).to_list()
    assert results_unordered[0].messages[0].content == "fast msg"
    assert results_unordered[1].messages[0].content == "slow msg"


def test_run_task_ignore_errors():
    """测试错误忽略逻辑"""
    ds = DatasetLoader.from_list([Conversation([Message("user", "err")])])

    # 1. ignore_errors=True: 不报错，返回空列表
    res = ds.run_task(ErrorProcessor(), ignore_errors=True).to_list()
    assert len(res) == 0

    # 2. ignore_errors=False: 应该抛出异常
    with pytest.raises(ValueError, match="Intentional Error"):
        ds.run_task(ErrorProcessor(), ignore_errors=False).to_list()


def test_run_task_checkpoint(tmp_path):
    """测试断点续传逻辑"""
    cp_file = tmp_path / "checkpoint.json"
    c1 = Conversation([Message("user", "msg1")])  # UID 会基于内容生成
    c2 = Conversation([Message("user", "msg2")])
    ds = DatasetLoader.from_list([c1, c2])

    proc = SlowProcessor()

    # 1. 第一次运行，只跑第 1 条，然后模拟中断（手动取第一条）
    # 注意：LazyDataset 只有在迭代时才会保存进度
    gen = ds.run_task(proc, checkpoint_path=str(cp_file), ordered=True)
    first_res = next(iter(gen))
    assert first_res.messages[0].content == "msg1"

    # 验证 checkpoint 文件里存了 c1 的 UID
    with open(cp_file, "r") as f:
        processed_ids = json.load(f)
        assert c1.get_uid() in processed_ids

    # 2. 第二次运行，应该自动跳过 c1，只跑 c2
    # 我们用一个计数器来证明 proc 只被调用了一次
    class CallCounterProcessor(BaseProcessor):
        def __init__(self):
            self.count = 0

        def process(self, conv):
            self.count += 1
            return conv

    counter_proc = CallCounterProcessor()
    final_res = ds.run_task(counter_proc, checkpoint_path=str(cp_file)).to_list()

    assert len(final_res) == 1
    assert final_res[0].messages[0].content == "msg2"
    assert counter_proc.count == 1  # 重点：c1 被跳过了，没进入 process
