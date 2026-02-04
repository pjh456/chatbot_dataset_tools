from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass(frozen=True)
class APIConfig:
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""


@dataclass(frozen=True)
class HTTPConfig:
    url: str = ""
    method: str = "GET"
    params: Optional[Dict] = None
    headers: Optional[Dict] = None
    json_data: Optional[Dict] = None
    data_path: List[str] = field(
        default_factory=lambda: ["data"]
    )  # 用于定位 JSON 响应中对话列表的键
    timeout: int = 60


@dataclass(frozen=True)
class ProcessingConfig:
    max_workers: int = 4
    batch_size: int = 32
    seed: int = 42


@dataclass(frozen=True)
class DatasetDefaults:
    role_map: Dict[str, str] = field(
        default_factory=lambda: {
            "user": "human",
            "assistant": "gpt",
            "system": "system",
        }
    )
    format: str = "jsonl"
    msg_sep: str = "\n"
    io_encoding: str = "utf-8"


@dataclass(frozen=True)
class GlobalSettings:
    api: APIConfig = APIConfig()
    http: HTTPConfig = HTTPConfig()
    proc: ProcessingConfig = ProcessingConfig()
    ds: DatasetDefaults = DatasetDefaults()
    extra: Dict[str, Any] = field(default_factory=dict)
