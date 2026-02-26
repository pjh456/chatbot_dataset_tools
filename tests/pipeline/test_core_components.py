import pytest
from chatbot_dataset_tools.registry import Registry
from chatbot_dataset_tools.pipeline.schema import PipelineConfig
from typing import Any


def test_registry_basic():
    """测试注册表的注册与获取"""
    reg = Registry[Any]("test_reg")

    @reg.register("one")
    def get_one():
        return 1

    @reg.register("two")
    class NumberTwo:
        pass

    assert reg.get("one") == get_one
    assert reg.get("two") == NumberTwo

    with pytest.raises(ValueError):
        reg.get("non_existent")


def test_pipeline_schema_variable_injection():
    """测试 Pipeline 配置中的变量替换 ${VAR}"""

    raw_config = {
        "name": "Test Job",
        "variables": {"ROOT": "/data", "DATE": "2023-01-01"},
        "steps": [
            {
                "name": "Load",
                "type": "loader",
                "params": {"path": "${ROOT}/file_${DATE}.jsonl"},
            }
        ],
    }

    # 模拟环境变量
    import os

    with pytest.MonkeyPatch().context() as m:
        m.setenv("ENV_VAR", "env_value")

        # 额外测试环境变量注入
        raw_config["variables"]["EXTRA"] = "${ENV_VAR}"

        cfg = PipelineConfig.from_dict(
            PipelineConfig._inject_variables(
                raw_config, {**os.environ, **raw_config["variables"]}
            )
        )

    assert cfg.name == "Test Job"
    # 验证变量是否被替换
    assert cfg.steps[0].params["path"] == "/data/file_2023-01-01.jsonl"
