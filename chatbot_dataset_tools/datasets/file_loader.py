import json
from pathlib import Path
from typing import Iterable, Iterator
from chatbot_dataset_tools.types import Conversation


class FileLoader(Iterable[Conversation]):
    def __init__(self, path: Path, format: str = "json"):
        self.path = path
        self.format = format

    def __iter__(self) -> Iterator[Conversation]:
        """每次调用 iter() 都会重新打开文件，从而支持多次遍历"""
        if self.format == "jsonl":
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield Conversation.from_dict(json.loads(line))
        else:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for conv_dict in data:
                    yield Conversation.from_dict(conv_dict)
