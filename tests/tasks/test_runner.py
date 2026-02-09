import time
from chatbot_dataset_tools.tasks.runner import TaskRunner
from chatbot_dataset_tools.tasks.processor import BaseProcessor
from chatbot_dataset_tools.types import Message, Conversation


class NothingProcessor(BaseProcessor):
    def process(self, conv: Conversation) -> Conversation | None:
        return conv


class SleepyProcessor(BaseProcessor):
    """模拟一个耗时的 AI 处理过程"""

    def process(self, conv: Conversation) -> Conversation:
        time.sleep(0.05)  # 模拟 AI 响应延迟
        return conv


class ErrorProcessor(BaseProcessor):
    """模拟一个会报错的算子"""

    def process(self, conv: Conversation) -> Conversation:
        raise ValueError("AI generation failed")


def test_runner_concurrency():
    """测试并发执行是否生效（耗时应远小于总和）"""
    processor = SleepyProcessor()
    runner = TaskRunner(processor, max_workers=5)

    data = [Conversation([Message("user", f"msg {i}")]) for i in range(10)]

    start = time.time()
    results = list(runner.run_stream(data))
    duration = time.time() - start

    assert len(results) == 10
    assert all(r.success for r in results)
    # 如果是串行执行，10 * 0.05 = 0.5s；并发执行应该接近 0.1 - 0.2s
    assert duration < 0.4


def test_runner_error_handling():
    """测试 Runner 是否能正确捕获异常而不中断流"""
    processor = ErrorProcessor()
    runner = TaskRunner(processor)

    data = [Conversation([Message("user", "test")])]
    results = list(runner.run_stream(data))

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error
    assert "AI generation failed" in results[0].error


def test_runner_rate_limit():
    """测试速率限制：每秒限制请求数"""
    processor = NothingProcessor()  # 瞬间完成
    # 限制为每秒 10 次请求 (间隔 0.1s)
    runner = TaskRunner(processor, rate_limit=10.0)

    data = [Conversation([Message("user", str(i))]) for i in range(3)]

    start = time.time()
    list(runner.run_stream(data))
    duration = time.time() - start

    # 3 条数据应该至少耗时 0.2s (第 1 条瞬发，第 2 条等 0.1s，第 3 条等 0.1s)
    assert duration >= 0.17
