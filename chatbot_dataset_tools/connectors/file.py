import json
from typing import Iterable, Iterator, Optional, Type
from .base import T, DataSource, DataSink
from .traits import FromDictType, ToDictType
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import FileConfig, config
from chatbot_dataset_tools.registry import register_source, register_sink
from chatbot_dataset_tools.utils import get_logger

logger = get_logger(__name__)


@register_source()
class FileSource(DataSource[T]):
    def __init__(
        self,
        file_cfg: Optional[FileConfig] = None,  # 允许传完整的 cfg
        conv_type: Type[FromDictType[T]] = Conversation,
        **overrides,  # 甚至允许传 encoding="gbk"
    ) -> None:
        base_cfg = config.current.settings.file
        if file_cfg:
            base_cfg = file_cfg
        self.file_cfg = base_cfg.derive(**overrides)
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

        logger.info(f"Loading data from file: {self.path} (format={self.format})")

        count = 0
        try:
            for item in loader_method():
                count += 1
                yield item
            logger.info(f"Loaded {count} items from {self.path}")
        except FileNotFoundError:
            logger.error(f"File not found: {self.path}")
            raise
        except Exception as e:
            logger.error(f"Error loading file {self.path}: {e}")
            raise

    def _load_json(self) -> Iterator[T]:
        with open(self.path, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Json Data Must be a list")

            for conv in data:
                yield self.conv_type.from_dict(conv)

    def _load_jsonl(self) -> Iterator[Conversation]:
        with open(self.path, "r", encoding=self.encoding) as f:
            for line in f:
                if line:
                    line = line.strip()
                    conv = json.loads(line)
                    yield self.conv_type.from_dict(conv)


@register_sink()
class FileSink(DataSink[T]):
    def __init__(self, file_cfg: Optional[FileConfig] = None, **overrides) -> None:
        base_cfg = config.current.settings.file
        if file_cfg:
            base_cfg = file_cfg
        self.file_cfg = base_cfg.derive(**overrides)

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
        logger.info(f"Saving to JSON file: {self.path}")
        count = 0

        try:
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
                    count += 1

                f.write("]")

                logger.info(f"Saved {count} items to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save to {self.path}: {e}")
            raise

    def _save_jsonl(self, data: Iterable[ToDictType]) -> None:
        logger.info(f"Saving to JSONL file: {self.path}")
        count = 0

        try:
            with open(self.path, "w", encoding=self.encoding) as f:
                for raw_conv in data:
                    conv = raw_conv.to_dict()
                    json.dump(conv, f)
                    f.write("\n")

            logger.info(f"Saved {count} items to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save to {self.path}: {e}")
            raise
