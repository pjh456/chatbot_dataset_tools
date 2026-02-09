# chatbot_dataset_tools/tasks/runner.py
import time
import threading
import concurrent.futures
from typing import Iterable, Iterator, Optional
from .processor import BaseProcessor
from .result import TaskResult
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import config


class TaskRunner:
    def __init__(
        self,
        processor: BaseProcessor,
        max_workers: Optional[int] = None,
        rate_limit: Optional[float] = None,
    ):
        self.processor = processor
        self.max_workers = max_workers or config.settings.proc.max_workers
        self.rate_limit = rate_limit or config.settings.task.rate_limit

        self._lock = threading.Lock()
        self._next_allowed_time = 0.0

    def _rate_limit_sleep(self):
        if self.rate_limit <= 0:
            return

        interval = 1.0 / self.rate_limit

        with self._lock:
            now = time.time()
            # 如果当前时间还没到“允许执行的时间”，就计算需要睡多久
            if now < self._next_allowed_time:
                wait_time = self._next_allowed_time - now
                time.sleep(wait_time)
                # 睡醒后，重新校准当前时间
                now = time.time()

            # 更新下一次任务允许开始的时间
            self._next_allowed_time = now + interval

    def run_stream(self, data: Iterable[Conversation]) -> Iterator[TaskResult]:
        """
        流式执行任务
        """
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 提交任务到线程池
            # 逻辑：将 processor 包装一层错误处理
            def safe_process(conv: Conversation) -> TaskResult:
                self._rate_limit_sleep()
                try:
                    start_time = time.time()
                    out = self.processor.process(conv)
                    return TaskResult(
                        success=True,
                        input=conv,
                        output=out,
                        metadata={"duration": time.time() - start_time},
                    )
                except Exception as e:
                    return TaskResult(success=False, input=conv, error=str(e))

            # 使用 map 保持顺序，或者使用 as_completed 提高效率
            # 目前使用 executor.map 的流式特性
            yield from executor.map(safe_process, data)
