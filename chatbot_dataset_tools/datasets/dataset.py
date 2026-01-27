from __future__ import annotations
from pathlib import Path
from typing import Optional, Iterator, Callable, TypeVar, Generic, TYPE_CHECKING
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import ConfigContext, GlobalSettings, config

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
        """并行执行 AI 处理（因为 IO 密集型操作单线程太慢）"""
        from concurrent.futures import ThreadPoolExecutor
        from .in_memory_dataset import InMemoryDataset

        # 优先级：参数 > 全局配置（proc.max_workers）
        workers = max_workers or config.settings.proc.max_workers

        items = self.to_list()
        # 在执行并行任务时，确保每个线程也能拿到正确的上下文（可选，取决于 func 是否依赖 config）
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(func, items))
        return InMemoryDataset(results, ctx=self.ctx)

    def to_jsonl(self, path: str | Path, encoding: Optional[str] = None) -> None:
        """将数据集保存为 jsonl 格式"""
        import json

        # 优先级：参数 > 绑定的设置
        path = Path(path)
        # 保存过程中应当使用数据集自身的属性而非最新的上下文！
        encoding = encoding or self.settings.ds.io_encoding

        with open(path, "w", encoding=encoding) as f:
            for item in self:
                json_line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")

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
