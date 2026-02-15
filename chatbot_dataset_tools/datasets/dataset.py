from __future__ import annotations
from pathlib import Path
from typing import Optional, Iterator, Callable, TypeVar, Generic, TYPE_CHECKING
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import ConfigContext, GlobalSettings, config
from chatbot_dataset_tools.connectors import DataSink, FileSink, HTTPSink
from chatbot_dataset_tools.tasks.processors import BaseProcessor
from chatbot_dataset_tools.tasks import CheckpointManager

T = TypeVar("T", bound=Conversation)

if TYPE_CHECKING:
    from .lazy_dataset import LazyDataset
    from .in_memory_dataset import InMemoryDataset


class Dataset(Generic[T]):
    """
    对话数据集抽象基类。

    配置模型：混合驱动模式 (Hybrid-Drive Mode)

    1. 静态绑定 (Sticky/Static Binding):
       数据集对象（如 .settings）始终绑定其创建时刻的 ConfigContext。
       这保证了数据集的固有属性（如 IO 编码、基础角色定义）在生命周期内的一致性。

    2. 动态响应 (Reactive Actions):
       即时性操作方法（如 .shuffle(), .sample()）会实时感知调用时刻的全局 config。
       允许开发者通过外部 contextmanager 动态干预算法参数（如 seed）。

    3. 过程外挂 (Injected Transformations):
       在执行 .map() 或 .filter() 等变换时，逻辑算子运行在“当前活跃上下文”中。
       这允许非侵入式地向变换逻辑注入配置（如 role_map），而无需改变数据集本身的血统。
       变换产生的结果数据集将继续继承父数据集的绑定上下文，实现配置的“血统延续”。
    """

    def __init__(self, ctx: Optional[ConfigContext] = None):
        # 捕获当前活跃的上下文，或者使用传入的上下文
        self._ctx = ctx or config.current

    @property
    def ctx(self) -> ConfigContext:
        return self._ctx

    @property
    def settings(self) -> GlobalSettings:
        return self._ctx.settings

    def with_config(self, **changes) -> Dataset[T]:
        """
        便捷方法：为当前数据集创建一个局部的配置变体。
        例如：ds.with_config(max_workers=8).parallel_map(...)
        """
        # 这里需要子类配合实现，或者简单的在子类中重写
        raise NotImplementedError

    def __iter__(self) -> Iterator[T]:
        raise NotImplementedError

    def __len__(self) -> int:
        """返回数据集长度，如果是惰性数据集，可以遍历计算"""
        raise NotImplementedError

    def map(self, func: Callable[[T], T]) -> Dataset[T]:
        raise NotImplementedError

    def parallel_map(
        self, func: Callable[[T], T], max_workers: int = 4
    ) -> InMemoryDataset[T]:
        """并行执行（IO 密集型操作单线程太慢）"""
        from concurrent.futures import ThreadPoolExecutor
        from .in_memory_dataset import InMemoryDataset

        # 优先级：参数 > 全局配置（proc.max_workers）
        workers = max_workers or config.settings.proc.max_workers

        items = self.to_list()
        # 在执行并行任务时，确保每个线程也能拿到正确的上下文（可选，取决于 func 是否依赖 config）
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(func, items))
        return InMemoryDataset(results, ctx=self.ctx)

    def run_task(
        self,
        processor: BaseProcessor,
        **overrides,
    ) -> LazyDataset[Conversation]:
        """
        并发执行任务的入口。.task > global_config
        Args:
            processor: 执行逻辑算子
            max_workers: 并发线程数
            rate_limit: 每秒请求限制
            ordered: 是否保持结果顺序 (True: 保持输入顺序; False: 谁快谁先出)
            ignore_errors: 是否忽略失败的任务 (True: 失败则丢弃; False: 失败抛出异常)
        """
        from chatbot_dataset_tools.tasks.runner import TaskRunner
        from .lazy_dataset import LazyDataset

        with config.switch(self.ctx):
            final_task_cfg = config.settings.task.derive(**overrides)

        runner = TaskRunner(processor, task_cfg=final_task_cfg)

        # 载入进度管理器
        cp_manager = None
        if final_task_cfg.checkpoint_path:
            cp_manager = CheckpointManager(final_task_cfg.checkpoint_path)

        # 定义结果生成器
        def result_generator():
            # 这里的 self 本身就是 iterable
            source_data = self

            if cp_manager:
                source_data = self.filter(lambda c: not cp_manager.is_processed(c.uid))  # type: ignore

            it = runner.run_stream(source_data)
            if final_task_cfg.show_progress:
                from tqdm import tqdm

                # 尝试获取总数，对于 LazyDataset 可能是 None
                total = None
                try:
                    total = len(source_data)
                except:
                    pass
                it = tqdm(
                    it, total=total, desc=f"Running {processor.__class__.__name__}"
                )

            for result in it:
                if result.success and result.output:
                    if cp_manager:
                        cp_manager.save(result.input.uid)

                    # 挂载执行元数据 (如耗时)
                    if hasattr(result.output, "metadata"):
                        result.output.metadata.update(result.metadata)

                    yield result.output
                elif not result.success:
                    if not final_task_cfg.ignore_errors:
                        raise RuntimeError(f"Task failed: {result.error}")
                    # TODO: 这里未来可以接入 Logger 模块记录失败 ID

        # 返回结果依然继承当前数据集的上下文
        return LazyDataset(result_generator(), ctx=self.ctx)

    def save_to(self, sink: DataSink[T]) -> None:
        """底层保存接口：接受任何实现了 DataSink 的对象"""
        sink.save(self)

    def to_json(self, path: str | Path, **kwargs) -> None:
        """
        快捷方式：保存输出为 JSON
        优先级处理：
        1. kwargs (显式传参) > 2. self.ctx (数据集绑定的配置) > 3. 全局默认配置
        """
        # 通过 switch 临时进入数据集自身的上下文
        with config.switch(self.ctx):
            # 在该上下文内创建 Sink，FileSink 内部会自动合并当前配置和 kwargs
            sink = FileSink(path=path, format="json", **kwargs)
            self.save_to(sink)

    def to_jsonl(self, path: str | Path, **kwargs) -> None:
        """
        快捷方式：保存输出为 JSONL
        优先级处理：
        1. kwargs (显式传参) > 2. self.ctx (数据集绑定的配置) > 3. 全局默认配置
        """
        # 通过 switch 临时进入数据集自身的上下文
        with config.switch(self.ctx):
            # 在该上下文内创建 Sink，FileSink 内部会自动合并当前配置和 kwargs
            sink = FileSink(path=path, format="jsonl", **kwargs)
            self.save_to(sink)

    def to_http(self, url: str, **kwargs) -> None:
        """
        快捷方式：保存输出为到远程
        优先级处理：
        1. kwargs (显式传参) > 2. self.ctx (数据集绑定的配置) > 3. 全局默认配置
        """
        # 通过 switch 临时进入数据集自身的上下文
        with config.switch(self.ctx):
            # 在该上下文内创建 Sink，HTTPSink 内部会自动合并当前配置和 kwargs
            sink = HTTPSink(url=url, **kwargs)
            self.save_to(sink)

    def filter(self, func: Callable[[T], bool]) -> Dataset[T]:
        raise NotImplementedError

    def to_list(self) -> list[T]:
        return list(self)

    def batch(self, batch_size: int) -> Iterator[list[T]]:
        batch: list[T] = []
        for item in self:
            batch.append(item)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def limit(self, n: int, from_begin: bool = True) -> LazyDataset[T]:
        """只取前/后 n 条数据 (调试神器)"""
        from .lazy_dataset import LazyDataset

        def generator():
            for i, item in enumerate(self):
                if from_begin:
                    if i >= n:
                        break
                else:
                    if len(self) - i > n:
                        continue
                yield item

        return LazyDataset(generator(), ctx=self.ctx)

    def shuffle(self, seed: Optional[int] = None) -> InMemoryDataset[T]:
        """打乱数据集。注意：这会将所有数据加载到内存。"""
        import random

        # 响应当前全局配置的 seed
        actual_seed = seed if seed is not None else config.settings.proc.seed
        data = self.to_list()

        random.seed(actual_seed)
        random.shuffle(data)
        from .in_memory_dataset import InMemoryDataset

        # 生成的子数据集保留原数据集配置
        return InMemoryDataset(data, ctx=self.ctx)

    def split(self, ratio: float) -> tuple[Dataset[T], Dataset[T]]:
        """按照比例切分数据集 (例如 0.8 将返回 80% 的训练集和 20% 的验证集)"""
        data = self.to_list()
        split_idx = int(len(data) * ratio)
        from .in_memory_dataset import InMemoryDataset

        return InMemoryDataset(data[:split_idx], ctx=self.ctx), InMemoryDataset(
            data[split_idx:], ctx=self.ctx
        )

    def sample(self, n: int, seed: int = 42) -> InMemoryDataset[T]:
        import random

        data = self.to_list()
        # 响应当前全局配置的 seed
        actual_seed = seed if seed is not None else config.settings.proc.seed

        random.seed(actual_seed)
        sampled_data = random.sample(data, min(n, len(data)))
        from .in_memory_dataset import InMemoryDataset

        return InMemoryDataset(sampled_data, ctx=self.ctx)
