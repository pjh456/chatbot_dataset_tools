import time
from chatbot_dataset_tools.tasks.runner import TaskRunner
from chatbot_dataset_tools.tasks.processor import BaseProcessor
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.config import TaskConfig


class VariableDelayProcessor(BaseProcessor):
    """根据输入内容决定睡眠时间的算子"""

    def process(self, conv: Conversation) -> Conversation:
        delay = float(conv.messages[0].content)
        time.sleep(delay)
        return conv


def test_runner_unordered_execution():
    """测试乱序执行：慢任务不应阻塞快任务"""
    processor = VariableDelayProcessor()

    # 任务1耗时 0.5s，任务2耗时 0.1s
    # 如果是 ordered=True，必须等 0.5s 才能拿到第一个结果
    # 如果是 ordered=False，0.1s 后应该能拿到第二个任务的结果
    data = [
        Conversation([Message("user", "0.5")]),
        Conversation([Message("user", "0.1")]),
    ]

    cfg = TaskConfig(max_workers=2, ordered_results=False)
    runner = TaskRunner(processor, task_cfg=cfg)

    start = time.time()
    results = list(runner.run_stream(data))
    duration = time.time() - start

    # 验证逻辑：
    # 1. 结果数量对
    assert len(results) == 2
    # 2. 第一个返回的一定是那个耗时 0.1s 的任务 (乱序生效)
    assert results[0].input.messages[0].content == "0.1"
    assert results[1].input.messages[0].content == "0.5"
    # 3. 总耗时应该是 max(0.5, 0.1) = 0.5s 左右 (并行生效)
    assert duration < 0.6


def test_token_bucket_rate_limit_concurrency():
    """
    核心测试：验证令牌桶是否实现了真正的 '锁外等待'。
    如果是在锁内等待，那么并发度会退化为 1。
    """

    class QuickProcessor(BaseProcessor):
        def process(self, conv: Conversation) -> Conversation:
            # 模拟极其快速的处理，主要时间花在限流等待上
            return conv

    # 目标：10 QPS (间隔 0.1s)
    # 数据：5 条
    # 理论总耗时： (5-1) * 0.1 = 0.4s (第1条不等待)
    cfg = TaskConfig(max_workers=4, rate_limit=10.0)
    runner = TaskRunner(QuickProcessor(), task_cfg=cfg)

    data = [Conversation([Message("user", str(i))]) for i in range(5)]

    start = time.time()
    list(runner.run_stream(data))
    duration = time.time() - start

    # 验证限流生效：不能太快
    assert duration >= 0.38
    # 验证没有串行化阻塞：如果是串行锁，且有调度开销，通常会显著慢于理论值
    # 这里宽容一点，只要不超过 0.6s 都算正常
    assert duration < 0.6


def test_thread_safety_shared_resource():
    """测试在并发环境下，多个 Processor 访问共享资源的安全性"""
    import threading

    class CounterProcessor(BaseProcessor):
        def __init__(self):
            self.lock = threading.Lock()
            self.count = 0

        def process(self, conv: Conversation) -> Conversation:
            # 模拟非原子操作：读 -> 睡 -> 写
            with self.lock:
                temp = self.count
                time.sleep(0.001)
                self.count = temp + 1
            return conv

    processor = CounterProcessor()
    # 开启高并发
    cfg = TaskConfig(max_workers=10, ordered_results=False)
    runner = TaskRunner(processor, task_cfg=cfg)

    count = 50
    data = [Conversation([Message("user", "")]) for _ in range(count)]

    list(runner.run_stream(data))

    # 如果线程不安全（Processor 自身没有锁），这里通常会小于 50
    # 这里主要测试 Runner 能够正确分发任务，且 Processor 自身的锁生效
    assert processor.count == count
