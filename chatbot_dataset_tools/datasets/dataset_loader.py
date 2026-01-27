import json
from pathlib import Path
from typing import Iterable, Optional
from chatbot_dataset_tools.types import Conversation
from .lazy_dataset import LazyDataset
from .in_memory_dataset import InMemoryDataset
from .file_loader import FileLoader
from chatbot_dataset_tools.config import config


class DatasetLoader:
    @staticmethod
    def from_json(
        path: str | Path, encoding: Optional[str] = None
    ) -> LazyDataset[Conversation]:
        # 显式捕获当前的 context
        current_ctx = config.current
        # 创建 loader 时注入 encoding
        loader = FileLoader(
            Path(path),
            format="json",
            encoding=encoding or current_ctx.settings.ds.io_encoding,
        )
        return LazyDataset(loader, ctx=current_ctx)

    @staticmethod
    def from_jsonl(
        path: str | Path, encoding: Optional[str] = None
    ) -> LazyDataset[Conversation]:
        # 显式捕获当前的 context
        current_ctx = config.current
        # 创建 loader 时注入 encoding
        loader = FileLoader(
            Path(path),
            format="jsonl",
            encoding=encoding or current_ctx.settings.ds.io_encoding,
        )
        return LazyDataset(loader, ctx=current_ctx)

    @staticmethod
    def from_list(
        conversations: Iterable[Conversation],
    ) -> InMemoryDataset[Conversation]:
        return InMemoryDataset(conversations, ctx=config.current)
