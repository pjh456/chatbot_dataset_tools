from __future__ import annotations
from typing import Optional, Iterable, Callable, Iterator
from .dataset import Dataset, T
from chatbot_dataset_tools.config import ConfigContext, config
from chatbot_dataset_tools.utils import get_logger

logger = get_logger(__name__)


class LazyDataset(Dataset[T]):
    """
    惰性数据集，适合大规模数据。
    map/filter 不会立即执行，而是堆叠算子。

    对于变换方法，为方便外部非侵入式配置过程，
    在变换过程中使用的是外部的最新上下文配置。

    数据集本身的属性在保存时保持不变，
    即产生的子数据集仍然是原数据集的上下文配置。

    对于迭代方法，其代表的是输入数据的属性，
    因此保留原有数据集的上下文配置。
    """

    def __init__(
        self, loader: Iterable[T], ops: list = [], ctx: Optional[ConfigContext] = None
    ):
        super().__init__(ctx)
        self._loader = loader

        # ops 是一个函数列表，每个函数接收一个迭代器并返回一个迭代器
        self._ops: list[Callable[[Iterable[T]], Iterable[T]]] = ops

    def __iter__(self) -> Iterator[T]:
        # 迭代时，才真正触发计算
        with config.switch(self.ctx):
            it = iter(self._loader)
            for op in self._ops:
                it = op(it)
            yield from it

    def with_config(self, **changes) -> LazyDataset[T]:
        return LazyDataset(self._loader, self._ops, ctx=self.ctx.clone(**changes))

    def __len__(self) -> int:
        # 惰性数据集无法预知长度
        raise TypeError(
            "LazyDataset has unknown length; convert to list first (e.g. ds.to_list())"
        )

    def map(self, func: Callable[[T], T]) -> LazyDataset[T]:
        func_name = getattr(func, "__name__", str(func))
        logger.debug(f"[Lazy] Stacking MAP op: {func_name}")

        new_op = lambda it, f=func: (f(x) for x in it)
        return LazyDataset(self._loader, self._ops + [new_op], ctx=self.ctx)

    def filter(self, func: Callable[[T], bool]) -> LazyDataset[T]:
        func_name = getattr(func, "__name__", str(func))
        logger.debug(f"[Lazy] Stacking FILTER op: {func_name}")

        new_op = lambda it, f=func: (x for x in it if f(x))
        return LazyDataset(self._loader, self._ops + [new_op], ctx=self.ctx)
