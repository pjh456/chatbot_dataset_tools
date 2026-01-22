from __future__ import annotations
from pathlib import Path
import json
from typing import Iterator, Callable, TypeVar, Generic, TYPE_CHECKING
from chatbot_dataset_tools.types import Conversation

T = TypeVar("T", bound=Conversation)

if TYPE_CHECKING:
    from .lazy_dataset import LazyDataset


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
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            for item in self:
                # 假设 item 是 Conversation 对象，调用其 to_dict 方法
                json_line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")

    def rename_roles(self, mapping: dict[str, str]) -> Dataset[T]:
        """批量重命名角色"""

        def _rename(conv: T) -> T:
            for msg in conv.messages:
                if msg.role in mapping:
                    msg.role = mapping[msg.role]
            return conv

        return self.map(_rename)

    def filter_turns(self, min_turns: int = -1, max_turns: int = -1) -> Dataset[T]:
        """过滤掉不在指定对话轮数范围的数据"""
        return self.filter(
            lambda conv: (len(conv.messages) >= min_turns if min_turns >= 0 else True)
            and (len(conv.messages) <= max_turns if max_turns >= 0 else True)
        )

    def limit(self, n: int) -> LazyDataset[T]:
        """只取前 n 条数据 (调试神器)"""
        from .lazy_dataset import LazyDataset

        def generator():
            for i, item in enumerate(self):
                if i >= n:
                    break
                yield item

        return LazyDataset(generator())
