import pytest
import time
from unittest.mock import patch
from chatbot_dataset_tools.datasets import DatasetLoader
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.tasks.processors import BaseProcessor
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.tasks import CheckpointManager

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
    cp_file = tmp_path / "checkpoint.txt"
    c1 = Conversation([Message("user", "msg1")])
    ds = DatasetLoader.from_list([c1])

    # 1. 运行任务
    # 设置 interval=1 确保立即写入，方便测试观察
    gen = ds.run_task(
        SlowProcessor(), checkpoint_path=str(cp_file), checkpoint_interval=1
    )
    next(iter(gen))

    # 2. 验证写入方式：现在是纯文本，每行一个 ID
    assert cp_file.exists()
    content = cp_file.read_text().strip()
    assert content == c1.get_uid()

    # 3. 验证追加性能 (手动模拟旧数据)
    with open(cp_file, "a") as f:
        f.write("old_id_123\n")

    manager = CheckpointManager(str(cp_file))
    assert manager.is_processed("old_id_123")
    assert manager.is_processed(c1.get_uid())


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
