import json
from pathlib import Path
from typing import Optional, Iterable, Iterator
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import config


class FileLoader(Iterable[Conversation]):
    def __init__(
        self, path: Path, format: str = "json", encoding: Optional[str] = None
    ):
        self.path = path
        self.format = format
        # 如果初始化没传 encoding，则锁定为那一刻的全局配置
        self.encoding = encoding or config.settings.ds.io_encoding

    def __iter__(self) -> Iterator[Conversation]:
        """每次调用 iter() 都会重新打开文件，从而支持多次遍历"""
        if self.format == "jsonl":
            with open(self.path, "r", encoding=self.encoding) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield Conversation.from_dict(json.loads(line))
        else:
            with open(self.path, "r", encoding=self.encoding) as f:
                data = json.load(f)
                for conv_dict in data:
                    yield Conversation.from_dict(conv_dict)
