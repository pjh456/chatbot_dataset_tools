from pathlib import Path
from typing import Iterable
from chatbot_dataset_tools.types import Conversation
from .lazy_dataset import LazyDataset
from .in_memory_dataset import InMemoryDataset
from .dataset import T
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.connectors import DataSource, FileSource, HTTPSource


class DatasetLoader:
    @staticmethod
    def from_source(source: DataSource[T]) -> LazyDataset[T]:
        """万能加载入口：支持 File, HTTP 等所有 DataSource"""

        class ReusableLoader:
            def __iter__(self):
                return source.load()

        # 捕获加载那一刻的全局配置作为数据集的出生配置
        return LazyDataset(ReusableLoader(), ctx=config.current)

    @staticmethod
    def from_json(path: str | Path, **kwargs) -> LazyDataset[Conversation]:
        # kwargs 允许覆盖 encoding, format 等
        source = FileSource(path=path, format="json", **kwargs)
        return DatasetLoader.from_source(source)

    @staticmethod
    def from_jsonl(path: str | Path, **kwargs) -> LazyDataset[Conversation]:
        # kwargs 允许覆盖 encoding, format 等
        source = FileSource(path=path, format="jsonl", **kwargs)
        return DatasetLoader.from_source(source)

    @staticmethod
    def from_http(url: str, **kwargs) -> LazyDataset[Conversation]:
        # kwargs 允许覆盖 encoding, format 等
        source = HTTPSource(url=url, **kwargs)
        return DatasetLoader.from_source(source)

    @staticmethod
    def from_list(
        conversations: Iterable[Conversation],
    ) -> InMemoryDataset[Conversation]:
        return InMemoryDataset(conversations, ctx=config.current)
