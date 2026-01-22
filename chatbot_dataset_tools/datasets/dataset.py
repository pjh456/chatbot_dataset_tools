from __future__ import annotations
from typing import Iterator, Callable, TypeVar, Generic
from chatbot_dataset_tools.types import Conversation

T = TypeVar("T", bound=Conversation)


class Dataset(Generic[T]):
    """对话数据集抽象接口"""

    def __iter__(self) -> Iterator[T]:
        raise NotImplementedError

    def __len__(self) -> int:
        """返回数据集长度，如果是惰性数据集，可以遍历计算"""
        raise NotImplementedError

    def map(self, func: Callable[[T], T]) -> Dataset[T]:
        raise NotImplementedError

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
