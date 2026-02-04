import json
from typing import Iterable, Iterator, Optional, Type
from .base import T, DataSource, DataSink
from .traits import FromDictType, ToDictType
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import FileConfig, config


class FileSource(DataSource[T]):
    def __init__(
        self,
        file_cfg: Optional[FileConfig] = None,
        conv_type: Type[FromDictType[T]] = Conversation,
    ) -> None:
        self.file_cfg = file_cfg or config.current.settings.file
        self.conv_type = conv_type

        self.path = self.file_cfg.path
        self.format = self.file_cfg.format.lower()
        self.encoding = self.file_cfg.encoding

    def load(self) -> Iterator[T]:
        method_name = f"_load_{self.format}"
        loader_method = getattr(self, method_name, None)

        if loader_method is None:
            raise NotImplementedError(
                f"FileSource does not support format: '{self.format}'. "
                f"Need to implement a method named '{method_name}'."
            )

        return loader_method()

    def _load_json(self) -> Iterator[T]:
        with open(self.path, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Json Data Must be a list")

            for conv in data:
                yield self.conv_type.from_dict(conv)

    def _load_jsonl(self) -> Iterator[T]:
        with open(self.path, "r", encoding=self.encoding) as f:
            for line in f:
                if line:
                    line = line.strip()
                    conv = json.loads(line)
                    yield self.conv_type.from_dict(conv)


class FileSink(DataSink[T]):
    def __init__(self, file_cfg: Optional[FileConfig] = None) -> None:
        self.file_cfg = file_cfg or config.current.settings.file

        self.path = self.file_cfg.path
        self.format = self.file_cfg.format.lower()
        self.encoding = self.file_cfg.encoding
        self.indent = self.file_cfg.indent

    def save(self, data: Iterable[ToDictType]) -> None:
        method_name = f"_save_{self.format}"
        saver_method = getattr(self, method_name, None)

        if saver_method is None:
            raise NotImplementedError(
                f"FileSink does not support format: '{self.format}'. "
                f"Need to implement a method named '{method_name}'."
            )

        return saver_method(data)

    def _save_json(self, data: Iterable[ToDictType]) -> None:
        with open(self.path, "w", encoding=self.encoding) as f:
            f.write("[")

            first = True
            for raw_conv in data:
                if not first:
                    f.write(",\n")
                else:
                    first = False

                conv = raw_conv.to_dict()
                json.dump(conv, f, ensure_ascii=False, indent=self.indent)

            f.write("]")

    def _save_jsonl(self, data: Iterable[ToDictType]) -> None:
        with open(self.path, "w", encoding=self.encoding) as f:
            for raw_conv in data:
                conv = raw_conv.to_dict()
                json.dump(conv, f)
                f.write("\n")
