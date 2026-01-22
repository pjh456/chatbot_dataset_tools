from __future__ import annotations
from typing import Iterable, Callable, Iterator
from .dataset import Dataset, T


class LazyDataset(Dataset[T]):
    """惰性数据集，适合大规模数据"""

    def __init__(self, loader: Iterable[T]):
        self._loader = loader
        self._ops: list[Callable[[Iterable[T]], Iterable[T]]] = []

    def __iter__(self) -> Iterator[T]:
        it: Iterable[T] = self._loader
        for op in self._ops:
            it = op(it)
        yield from it

    def __len__(self):
        raise TypeError("LazyDataset has unknown length; convert to list first")

    def map(self, func: Callable[[T], T]) -> LazyDataset[T]:
        new_ds = LazyDataset(self._loader)
        new_ds._ops = self._ops + [lambda it: (func(x) for x in it)]
        return new_ds

    def filter(self, func: Callable[[T], bool]) -> LazyDataset[T]:
        new_ds = LazyDataset(self._loader)
        new_ds._ops = self._ops + [lambda it: (x for x in it if func(x))]
        return new_ds
