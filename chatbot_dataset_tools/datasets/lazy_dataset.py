from __future__ import annotations
from typing import Optional, Iterable, Callable, Iterator
from .dataset import Dataset, T
from chatbot_dataset_tools.config import ConfigContext, config


class LazyDataset(Dataset[T]):
    """
    惰性数据集，适合大规模数据。

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
        self._ops: list[Callable[[Iterable[T]], Iterable[T]]] = ops

    def __iter__(self) -> Iterator[T]:
        with config.switch(self.ctx):
            it = iter(self._loader)
            for op in self._ops:
                it = op(it)
            yield from it

    def with_config(self, **changes) -> LazyDataset[T]:
        return LazyDataset(self._loader, self._ops, ctx=self.ctx.clone(**changes))

    def __len__(self):
        raise TypeError("LazyDataset has unknown length; convert to list first")

    def map(self, func: Callable[[T], T]) -> LazyDataset[T]:
        new_op = lambda it, f=func: (f(x) for x in it)
        return LazyDataset(self._loader, self._ops + [new_op], ctx=self.ctx)

    def filter(self, func: Callable[[T], bool]) -> LazyDataset[T]:
        new_op = lambda it, f=func: (x for x in it if f(x))
        return LazyDataset(self._loader, self._ops + [new_op], ctx=self.ctx)
