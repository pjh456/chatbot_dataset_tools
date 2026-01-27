from __future__ import annotations
from typing import Optional, Iterable, Callable, Iterator
from .dataset import Dataset, T
from chatbot_dataset_tools.config import ConfigContext, config


class InMemoryDataset(Dataset[T]):
    """
    一次性加载到内存的数据集。

    对于变换方法，为方便外部非侵入式配置过程，
    在变换过程中使用的是外部的最新上下文配置。

    数据集本身的属性在保存时保持不变，
    即产生的子数据集仍然是原数据集的上下文配置！

    对于迭代方法，其代表的是输入数据的属性，
    因此保留原有数据集的上下文配置。
    """

    def __init__(self, items: Iterable[T], ctx: Optional[ConfigContext] = None):
        super().__init__(ctx)
        self._data = list(items)

    def __iter__(self) -> Iterator[T]:
        with config.switch(self.ctx):
            yield from iter(self._data)

    def with_config(self, **changes) -> InMemoryDataset[T]:
        return InMemoryDataset(self._data, ctx=self.ctx.clone(**changes))

    def __len__(self) -> int:
        return len(self._data)

    def map(self, func: Callable[[T], T]) -> InMemoryDataset[T]:
        with config.switch(self.ctx):
            new_data = [func(item) for item in self._data]
        return InMemoryDataset(new_data, ctx=self.ctx)

    def filter(self, func: Callable[[T], bool]) -> InMemoryDataset[T]:
        with config.switch(self.ctx):
            new_data = [item for item in self._data if func(item)]
        return InMemoryDataset(new_data, ctx=self.ctx)
