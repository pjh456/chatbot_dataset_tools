import pytest
import time
import json
from unittest.mock import patch
from chatbot_dataset_tools.datasets import DatasetLoader
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.tasks.processors import BaseProcessor
from chatbot_dataset_tools.config import config

# --- 准备工作：定义测试用的 Processor ---


class SlowProcessor(BaseProcessor):
    """模拟耗时任务"""

    def process(self, conv: Conversation) -> Conversation:
        if "slow" in conv.messages[0].content:
            time.sleep(0.1)
        return conv


class ErrorProcessor(BaseProcessor):
    """模拟报错任务"""

    def process(self, conv: Conversation) -> Conversation:
        raise ValueError("Intentional Error")


# --- 功能测试 (Functional Tests) ---


def test_run_task_ordered():
    """测试 ordered_results=True (默认)"""
    c1 = Conversation([Message("user", "slow msg")])
    c2 = Conversation([Message("user", "fast msg")])
    ds = DatasetLoader.from_list([c1, c2])

    # 注意：参数名必须是 ordered_results，对应 TaskConfig 字段
    results = ds.run_task(
        SlowProcessor(), max_workers=2, ordered_results=True
    ).to_list()

    assert results[0].messages[0].content == "slow msg"
    assert results[1].messages[0].content == "fast msg"


def test_run_task_unordered():
    """测试 ordered_results=False (谁快谁先出)"""
    c1 = Conversation([Message("user", "slow msg")])
    c2 = Conversation([Message("user", "fast msg")])
    ds = DatasetLoader.from_list([c1, c2])

    # 注意：参数名必须是 ordered_results
    results = ds.run_task(
        SlowProcessor(), max_workers=2, ordered_results=False
    ).to_list()

    # fast msg 应该先出来
    assert results[0].messages[0].content == "fast msg"
    assert results[1].messages[0].content == "slow msg"


def test_run_task_ignore_errors():
    """测试错误处理配置"""
    ds = DatasetLoader.from_list([Conversation([Message("user", "err")])])

    # 1. 测试忽略错误 (TaskConfig.ignore_errors 默认为 True)
    # 显式传入以确保不受全局配置干扰
    res = ds.run_task(ErrorProcessor(), ignore_errors=True).to_list()
    assert len(res) == 0

    # 2. 测试不忽略错误
    # TaskRunner 会抛出原始异常 (ValueError)
    with pytest.raises(ValueError, match="Intentional Error"):
        ds.run_task(ErrorProcessor(), ignore_errors=False).to_list()


def test_run_task_checkpoint(tmp_path):
    """测试断点续传逻辑"""
    cp_file = tmp_path / "checkpoint.json"
    c1 = Conversation([Message("user", "msg1")])
    c2 = Conversation([Message("user", "msg2")])
    ds = DatasetLoader.from_list([c1, c2])

    # 1. 运行并生成 checkpoint
    # 模拟只处理了第一个就退出的情况
    gen = ds.run_task(SlowProcessor(), checkpoint_path=str(cp_file))
    next(iter(gen))

    # 验证文件生成
    assert cp_file.exists()

    # 2. 第二次运行，计数器验证
    class CounterProc(BaseProcessor):
        def __init__(self):
            self.count = 0

        def process(self, conv):
            self.count += 1
            return conv

    proc = CounterProc()
    # 重新运行，传入相同的 checkpoint_path
    ds.run_task(proc, checkpoint_path=str(cp_file)).to_list()

    # msg1 被跳过，只处理了 msg2
    assert proc.count == 1


# --- 配置集成测试 (Integration Tests with Config) ---


def test_task_config_inheritance():
    """
    核心测试：验证 Dataset 绑定的配置能否自动流转到 TaskRunner
    """
    ds = DatasetLoader.from_list([Conversation([Message("user", "test")])])

    # 1. 使用 with_config 绑定特定任务配置
    # 我们设置一个非默认值：max_workers=1, rate_limit=5.0
    ds_bound = ds.with_config(
        task={"max_workers": 1, "rate_limit": 5.0, "show_progress": False}
    )

    # 2. Mock TaskRunner 来拦截传入的配置
    with patch("chatbot_dataset_tools.tasks.runner.TaskRunner") as MockRunner:
        # 必须让 MockRunner 的实例返回一个空的迭代器，否则 run_stream 会报错
        mock_instance = MockRunner.return_value
        mock_instance.run_stream.return_value = iter([])

        # 执行 run_task，不传任何参数
        ds_bound.run_task(SlowProcessor()).to_list()

        # 3. 验证 TaskRunner 收到的配置
        # args[0] 是 processor, kwargs['task_cfg'] 是配置对象
        _, kwargs = MockRunner.call_args
        task_cfg = kwargs.get("task_cfg")

        assert task_cfg is not None
        assert task_cfg.max_workers == 1
        assert task_cfg.rate_limit == 5.0
        assert task_cfg.show_progress is False


def test_task_arg_priority():
    """
    核心测试：验证 参数传递 > 绑定配置 > 全局配置
    """
    # 全局默认 max_workers=4 (假设)
    ds = DatasetLoader.from_list([Conversation([Message("user", "test")])])

    # 绑定配置 max_workers=2
    ds_bound = ds.with_config(task={"max_workers": 2})

    with patch("chatbot_dataset_tools.tasks.runner.TaskRunner") as MockRunner:
        mock_instance = MockRunner.return_value
        mock_instance.run_stream.return_value = iter([])

        # 显式参数 max_workers=8
        ds_bound.run_task(SlowProcessor(), max_workers=8).to_list()

        _, kwargs = MockRunner.call_args
        task_cfg = kwargs.get("task_cfg")

        # 应该取 8
        assert task_cfg.max_workers == 8


def test_progress_bar_toggle():
    """测试 show_progress 参数控制"""
    ds = DatasetLoader.from_list([Conversation([Message("user", "test")])])

    # 我们通过 mock tqdm 来验证它是否被调用
    with patch("tqdm.tqdm") as mock_tqdm:
        # case 1: show_progress=False
        ds.run_task(SlowProcessor(), show_progress=False).to_list()
        mock_tqdm.assert_not_called()

        # case 2: show_progress=True (默认值，或者显式指定)
        ds.run_task(SlowProcessor(), show_progress=True).to_list()
        mock_tqdm.assert_called()
