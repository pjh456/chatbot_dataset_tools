from __future__ import annotations
from pathlib import Path
from typing import Iterator, Callable, TypeVar, Generic, TYPE_CHECKING
from chatbot_dataset_tools.types import Conversation

T = TypeVar("T", bound=Conversation)

if TYPE_CHECKING:
    from .lazy_dataset import LazyDataset
    from .in_memory_dataset import InMemoryDataset


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

    def to_jsonl(self, path: str | Path) -> None:
        """将数据集保存为 jsonl 格式"""
        import json

        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            for item in self:
                json_line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")

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

        return LazyDataset(generator())

    def shuffle(self, seed: int = 42) -> InMemoryDataset[T]:
        """打乱数据集。注意：这会将所有数据加载到内存。"""
        import random

        data = self.to_list()
        random.seed(seed)
        random.shuffle(data)
        from .in_memory_dataset import InMemoryDataset

        return InMemoryDataset(data)

    def split(self, ratio: float) -> tuple[Dataset[T], Dataset[T]]:
        """按照比例切分数据集 (例如 0.8 将返回 80% 的训练集和 20% 的验证集)"""
        data = self.to_list()
        split_idx = int(len(data) * ratio)
        from .in_memory_dataset import InMemoryDataset

        return InMemoryDataset(data[:split_idx]), InMemoryDataset(data[split_idx:])

    def sample(self, n: int, seed: int = 42) -> InMemoryDataset[T]:
        import random

        data = self.to_list()
        random.seed(seed)
        sampled_data = random.sample(data, min(n, len(data)))
        from .in_memory_dataset import InMemoryDataset

        return InMemoryDataset(sampled_data)
