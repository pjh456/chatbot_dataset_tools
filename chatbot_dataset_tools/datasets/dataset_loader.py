import json
from pathlib import Path
from typing import Iterable
from chatbot_dataset_tools.types import Conversation
from .lazy_dataset import LazyDataset
from .in_memory_dataset import InMemoryDataset
from .file_loader import FileLoader


class DatasetLoader:
    @staticmethod
    def from_json(path: str | Path) -> LazyDataset[Conversation]:
        return LazyDataset(FileLoader(Path(path), format="json"))

    @staticmethod
    def from_jsonl(path: str | Path) -> LazyDataset[Conversation]:
        return LazyDataset(FileLoader(Path(path), format="jsonl"))

    @staticmethod
    def from_list(
        conversations: Iterable[Conversation],
    ) -> InMemoryDataset[Conversation]:
        return InMemoryDataset(conversations)
