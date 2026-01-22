from __future__ import annotations
from typing import Iterable, Callable, Iterator
from .dataset import Dataset, T


class InMemoryDataset(Dataset[T]):
    """一次性加载到内存的数据集"""

    def __init__(self, items: Iterable[T]):
        self._data = list(items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def map(self, func: Callable[[T], T]) -> InMemoryDataset[T]:
        return InMemoryDataset(func(c) for c in self._data)

    def filter(self, func: Callable[[T], bool]) -> InMemoryDataset[T]:
        return InMemoryDataset(c for c in self._data if func(c))
