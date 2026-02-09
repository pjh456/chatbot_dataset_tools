from abc import ABC, abstractmethod
from typing import Iterator, Iterable, TypeVar, Generic
from chatbot_dataset_tools.types import Conversation

T = TypeVar("T", bound=Conversation)


class DataSource(Generic[T], ABC):
    @abstractmethod
    def load(self) -> Iterator[T]: ...


class DataSink(Generic[T], ABC):
    @abstractmethod
    def save(self, data: Iterable[T]) -> None: ...
