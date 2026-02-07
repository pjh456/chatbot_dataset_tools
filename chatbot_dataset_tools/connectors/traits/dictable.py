from typing import Mapping, Any, TypeVar, Protocol

T_dictable = TypeVar("T_dictable", covariant=True)


class FromDictType(Protocol[T_dictable]):
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> T_dictable: ...


class ToDictType(Protocol):
    def to_dict(self) -> dict[str, Any]: ...
