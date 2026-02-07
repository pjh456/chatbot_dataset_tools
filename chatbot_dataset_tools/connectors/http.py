import json
import httpx
from typing import (
    Any,
    Iterable,
    Iterator,
    Optional,
    Dict,
    List,
    Union,
    Type,
    Sequence,
    Mapping,
)
from .base import T, DataSource, DataSink
from .traits import FromDictType, ToDictType
from chatbot_dataset_tools.types import Conversation
from chatbot_dataset_tools.config import HTTPConfig, config


class HTTPSource(DataSource[T]):
    def __init__(
        self,
        http_cfg: Optional[HTTPConfig] = None,
        conv_type: Type[FromDictType[T]] = Conversation,
    ):
        self.http_cfg = http_cfg or config.current.settings.http
        self.conv_type = conv_type

        self.url = self.http_cfg.url
        self.method = self.http_cfg.method
        self.params = self.http_cfg.params
        self.headers = self.http_cfg.headers
        self.json_data = self.http_cfg.json_data
        self.data_path = self.http_cfg.data_path
        self.timeout = self.http_cfg.timeout

    def load(self) -> Iterator[T]:
        with httpx.Client(timeout=self.timeout) as cli:
            resp = cli.request(
                method=self.method,
                url=self.url,
                params=self.params,
                headers=self.headers,
                json=self.json_data,
            )
            resp.raise_for_status()

            raw_data: Dict | List = resp.json()

            for path in self.data_path:
                if isinstance(path, str) and isinstance(raw_data, Dict):
                    raw_data = raw_data.get(path, {})
                elif isinstance(path, int) and isinstance(raw_data, List):
                    raw_data = raw_data[path]
                else:
                    raise ValueError(
                        f"Response data path '{path}' invalid for current structure!"
                    )

            if not isinstance(raw_data, list):
                raise ValueError(
                    f"Expected a list of conversations at path {self.data_path}, got {type(raw_data)}"
                )

            for item in raw_data:
                yield self.conv_type.from_dict(item)


class HTTPSink(DataSink[T]):
    def __init__(self, http_cfg: Optional[HTTPConfig] = None):
        self.http_cfg = http_cfg or config.current.settings.http

        self.url = self.http_cfg.url
        self.method = self.http_cfg.method
        self.params = self.http_cfg.params
        self.headers = self.http_cfg.headers
        self.data_path = self.http_cfg.data_path
        self.timeout = self.http_cfg.timeout

    def save(self, data: Iterable[ToDictType]) -> None:
        payload_list = [item.to_dict() for item in data]

        final_json = self._wrap_data(payload_list)

        with httpx.Client(timeout=self.timeout) as cli:
            resp = cli.request(
                method=self.method,
                url=self.url,
                params=self.params,
                headers=self.headers,
                json=final_json,
            )
            resp.raise_for_status()

    def save_streaming(self, data: Iterable[ToDictType]) -> None:
        """
        逐条发送数据。如果数据集非常大，推荐使用此方法。
        """
        with httpx.Client(timeout=self.timeout) as cli:
            for item in data:
                resp = cli.request(
                    method=self.method,
                    url=self.url,
                    params=self.params,
                    headers=self.headers,
                    json=item.to_dict(),
                )
                resp.raise_for_status()

    def _wrap_data(
        self, data_list: Sequence[Mapping[str, Any]]
    ) -> Union[Sequence[Any], Mapping[str, Any]]:
        """根据 data_path 将列表包装进嵌套字典中"""
        if not self.data_path:
            return data_list

        # 逆向构建，例如 path=["a", "b"] -> {"a": {"b": data_list}}
        res = data_list
        for key in reversed(self.data_path):
            if isinstance(key, str):
                res = {key: res}
            else:
                # TODO: 支持路径中有 index
                continue

        return res
