from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import os
import re
from chatbot_dataset_tools.utils import get_logger

logger = get_logger(__name__)


@dataclass
class StepConfig:
    name: str
    type: str  # loader, map, filter, task, saver, router
    # 允许 params 里包含具体的参数，也允许包含子步骤（给 router 用）
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    name: str
    steps: List[StepConfig]
    description: Optional[str] = None

    # 允许在 Pipeline JSON 中临时覆盖全局配置
    settings: Dict[str, Any] = field(default_factory=dict)
    # 定义 Pipeline 内部变量，用于替换 ${var}
    variables: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "PipelineConfig":
        logger.info(f"Loading Pipeline config from: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except FileNotFoundError:
            logger.critical(f"Pipeline config file not found: {path}")
            raise
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON in pipeline config: {e}")
            raise

        # 1. 预处理：变量替换
        # 优先使用 JSON 里定义的 variables，其次使用 环境变量
        defined_vars = raw_data.get("variables", {})
        env_vars = dict(os.environ)
        # 合并变量池：JSON 内部变量优先级 > 环境变量
        context_vars = {**env_vars, **defined_vars}

        # 打印可用的变量键（不打印值，防止泄露密钥）
        logger.debug(f"Available context variables: {list(context_vars.keys())}")

        resolved_data = cls._inject_variables(raw_data, context_vars)

        step_count = len(resolved_data.get("steps", []))
        logger.info(f"Config loaded. Found {step_count} steps.")

        return cls.from_dict(resolved_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        steps_data = data.get("steps", [])
        steps = [
            StepConfig(
                name=s.get("name", f"step_{i}"),
                type=s.get("type", "unknown"),
                params=s.get("params", {}),
            )
            for i, s in enumerate(steps_data)
        ]
        return cls(
            name=data.get("name", "Unnamed Pipeline"),
            description=data.get("description"),
            settings=data.get("settings", {}),
            variables=data.get("variables", {}),
            steps=steps,
        )

    @staticmethod
    def _inject_variables(data: Any, vars_map: Dict[str, str]) -> Any:
        """递归遍历字典/列表，替换字符串中的 ${VAR}"""
        if isinstance(data, str):
            # 查找 ${VAR} 模式
            def replacer(match):
                key = match.group(1)
                val = vars_map.get(key)

                # 变量未找到时给出警告
                if val is None:
                    logger.warning(
                        f"Variable '${{{key}}}' not found in context! Keeping original string."
                    )
                    return match.group(0)

                # TODO: 记录替换（仅在 DEBUG 模式，且尽量模糊处理值）

                return str(val)

            new_str = re.sub(r"\$\{(.*?)\}", replacer, data)
            return new_str

        elif isinstance(data, dict):
            return {
                k: PipelineConfig._inject_variables(v, vars_map)
                for k, v in data.items()
            }

        elif isinstance(data, list):
            return [PipelineConfig._inject_variables(item, vars_map) for item in data]

        return data
