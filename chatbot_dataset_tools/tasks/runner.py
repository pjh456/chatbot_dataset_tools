import time
import concurrent.futures
from typing import Iterable, Iterator, Optional
from .result import TaskResult
from .processors import BaseProcessor
from .limiter import TokenBucketLimiter
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import config, TaskConfig


class TaskRunner:
    def __init__(
        self,
        processor: BaseProcessor,
        task_cfg: Optional[TaskConfig] = None,
        **overrides  # 允许直接传 max_workers 等
    ):
        # 1. 配置合并逻辑
        global_task_cfg = config.settings.task
        base_cfg = task_cfg or global_task_cfg
        self.cfg = base_cfg.derive(**overrides)

        self.processor = processor
        self.limiter = TokenBucketLimiter(self.cfg.rate_limit)

    def _safe_process(self, conv: Conversation) -> TaskResult:
        """包装单个处理逻辑：限流 -> 执行 -> 捕获异常"""
        # 1. 执行限流等待 (锁外睡眠)
        self.limiter.wait()

        try:
            start_time = time.time()
            # 2. 执行核心逻辑
            out = self.processor.process(conv)
            duration = time.time() - start_time

            return TaskResult(
                success=True, input=conv, output=out, metadata={"duration": duration}
            )
        except Exception as e:
            # 错误处理
            if not self.cfg.ignore_errors:
                raise e
            return TaskResult(success=False, input=conv, error=str(e))

    def run_stream(self, data: Iterable[Conversation]) -> Iterator[TaskResult]:
        """根据配置决定是顺序返回还是乱序返回"""

        # 必须把 iterable 转为 iterator，防止多次消费
        # 注意：如果是 LazyDataset，这里不会立即加载所有数据，依然是流式的

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.cfg.max_workers
        ) as executor:
            if self.cfg.ordered_results:
                # 模式 A: 保持顺序 (类似于之前的 map)
                yield from executor.map(self._safe_process, data)
            else:
                # 模式 B: 乱序 (谁先完成谁先返回，吞吐量最大)
                # 注意：这里需要先把所有任务提交进去，这会消耗内存来存储 Future 对象
                # TODO: 对于超大数据集，使用分批 submission，这里暂实现标准版
                futures = {
                    executor.submit(self._safe_process, item): item for item in data
                }

                for future in concurrent.futures.as_completed(futures):
                    yield future.result()
