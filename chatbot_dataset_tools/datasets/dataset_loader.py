import json
from pathlib import Path
from typing import Iterable
from chatbot_dataset_tools.types import Conversation
from .lazy_dataset import LazyDataset
from .in_memory_dataset import InMemoryDataset


class DatasetLoader:
    @staticmethod
    def from_json(path: str | Path) -> LazyDataset[Conversation]:
        path = Path(path)

        def generator():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for conv_dict in data:
                    yield Conversation.from_dict(conv_dict)

        return LazyDataset(generator())

    @staticmethod
    def from_list(
        conversations: Iterable[Conversation],
    ) -> InMemoryDataset[Conversation]:
        return InMemoryDataset(conversations)
