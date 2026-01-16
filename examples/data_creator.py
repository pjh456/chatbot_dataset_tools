from dotenv import load_dotenv
import os
from pathlib import Path
import json
from typing import Dict, Any

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_PATH, "..", ".env"), override=True)

API_KEY: str = os.getenv("API_KEY", "")
API_BASE_URL: str = os.getenv("API_BASE_URL", "")
API_MODEL: str = os.getenv("API_MODEL", "")


def load_prompt_from_env(env_key: str) -> str:
    path = os.getenv(env_key)
    if not path:
        raise RuntimeError(f"Missing prompt path env: {env_key}")
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"Prompt file not found: {p}")
    return p.read_text(encoding="utf-8")


CHARACTER_SYSTEM_PROMPT = load_prompt_from_env("CHARACTER_PROMPT_PATH")


def load_json_from_env(env_key: str) -> Dict[Any, Any]:
    path = os.getenv(env_key)
    if not path:
        raise RuntimeError(f"Missing prompt path env: {env_key}")
    p = Path(os.path.join(BASE_PATH, "..", path))
    if not p.exists():
        raise RuntimeError(f"Prompt file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


schema = load_json_from_env("SCHEMA_PATH")
RESPONSE_SCHEMA = schema["response"]
EVENT_BASES = schema["event_bases"]
SLOTS = schema["slots"]
ENV_MODIFIERS = schema["modifiers"]

from chatbot_dataset_tools.api import APIClient
from chatbot_dataset_tools.adapters import AlpacaAdapter
from chatbot_dataset_tools.generator import (
    ResponseMapper,
    MessageMapping,
    ScenarioManager,
    ScenarioFactory,
    DataSynthesizer,
    GenerationTaskRunner,
    setup_persistence,
)


# 1. 初始化各组件
api_client = APIClient(api_key=API_KEY, base_url=API_BASE_URL, model=API_MODEL)
synthesizer = DataSynthesizer(api_client)
scenario_mgr = ScenarioManager(bases=EVENT_BASES, slots=SLOTS, modifiers=ENV_MODIFIERS)
factory = ScenarioFactory(scenario_mgr)

# 2. 设置保存逻辑 (Alpaca 格式, 带 History)
adapter = AlpacaAdapter(use_history=True)
start_idx, save_callback = setup_persistence(
    os.path.join(BASE_PATH, "..", "prompts", "data"), adapter
)

# 3. 配置映射关系
mapper = ResponseMapper(
    items_path="turns",
    message_mapping=MessageMapping(
        role_map={"jiangchen": "user", "murasame": "assistant"}
    ),
)

# 4. 运行
runner = GenerationTaskRunner(synthesizer, max_workers=1)
runner.run_batch(
    total_goal=1,
    system_prompt=CHARACTER_SYSTEM_PROMPT,
    schema=RESPONSE_SCHEMA,
    mapper=mapper,
    prompt_factory=factory.produce,
    on_success=save_callback,
    start_idx=start_idx,
)
