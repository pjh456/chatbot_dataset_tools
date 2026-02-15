from dataclasses import dataclass, field, replace, fields
from typing import Dict, Any, Optional, List, TypeVar, Type
from pathlib import Path

T = TypeVar("T", bound="BaseConfig")


@dataclass(frozen=True)
class BaseConfig:
    def derive(self: T, **changes) -> T:
        """通用的衍生方法，自动过滤掉不属于该类的字段"""
        valid_keys = {f.name for f in fields(self)}
        # 只取当前类存在的字段进行 replace
        filtered_changes = {k: v for k, v in changes.items() if k in valid_keys}
        if not filtered_changes:
            return self
        return replace(self, **filtered_changes)


@dataclass(frozen=True)
class APIConfig(BaseConfig):
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""


@dataclass(frozen=True)
class ProcessingConfig(BaseConfig):
    max_workers: int = 4
    batch_size: int = 32
    seed: int = 42


@dataclass(frozen=True)
class FileConfig(BaseConfig):
    path: str | Path = ""
    format: str = "jsonl"
    encoding: str = "utf-8"
    indent: int = 2


@dataclass(frozen=True)
class HTTPConfig(BaseConfig):
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
class TaskConfig(BaseConfig):
    # 核心并发控制
    max_workers: int = 4  # 线程池大小
    rate_limit: float = 0.0  # TPS/QPS 限制 (0 表示不限制)

    # 行为控制
    ordered_results: bool = (
        True  # True: 保持输入输出顺序一致; False: 谁先完成谁先返回(吞吐量更高)
    )

    max_retries: int = 3  # 失败重试次数
    ignore_errors: bool = True  # 是否忽略错误继续执行

    checkpoint_interval: int = 10  # 每处理多少条记录记录一次进度
    checkpoint_path: str = ""  # 进度保存文件路径
    show_progress: bool = True  # 是否显示进度条


@dataclass(frozen=True)
class DatasetDefaults(BaseConfig):
    role_map: Dict[str, str] = field(
        default_factory=lambda: {
            "user": "human",
            "assistant": "gpt",
            "system": "system",
        }
    )
    msg_sep: str = "\n"


@dataclass(frozen=True)
class GlobalSettings(BaseConfig):
    api: APIConfig = APIConfig()
    http: HTTPConfig = HTTPConfig()
    proc: ProcessingConfig = ProcessingConfig()
    file: FileConfig = FileConfig()
    task: TaskConfig = TaskConfig()
    ds: DatasetDefaults = DatasetDefaults()
    extra: Dict[str, Any] = field(default_factory=dict)

    def derive(self, **changes) -> "GlobalSettings":
        """
        深度衍生：支持平铺参数 (path="...") 或 嵌套字典/对象 (ds={"role_map": ...})
        """
        new_values = {}

        for f in fields(self):
            current_section = getattr(self, f.name)

            # 仅对继承了 BaseConfig 的子配置类进行递归衍生逻辑
            if isinstance(current_section, BaseConfig):
                # 情况 1：显式传了该 section 的配置，例如 ds={...} 或 ds=DatasetDefaults(...)
                if f.name in changes:
                    provided = changes[f.name]
                    if isinstance(provided, dict):
                        # 如果传的是字典，则调用子对象的 derive 进行增量更新
                        new_values[f.name] = current_section.derive(**provided)
                    else:
                        # 如果传的是完整的 BaseConfig 对象，直接替换
                        new_values[f.name] = provided
                else:
                    # 情况 2：没传该 section，但可能传了平铺参数，例如直接传了 role_map={...}
                    # 我们把整个 changes 丢给子类的 derive，由它过滤出自己关心的字段
                    new_values[f.name] = current_section.derive(**changes)
            else:
                # 对于 extra 等非 BaseConfig 字段，如果 changes 里有，则直接更新
                if f.name in changes:
                    new_values[f.name] = changes[f.name]

        return replace(self, **new_values)
