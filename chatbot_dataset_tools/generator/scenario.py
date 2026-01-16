import random
from typing import List, Dict, Any


class ScenarioManager:
    """负责场景的组合与变量注入"""

    def __init__(
        self, bases: List[str], slots: Dict[str, List[str]], modifiers: List[str]
    ):
        self.bases = bases
        self.slots = slots
        self.modifiers = modifiers

    def get_random_context(self) -> Dict[str, str | Dict[str, str]]:
        """返回一个包含场景描述和元数据的字典"""
        base_tmpl = random.choice(self.bases)
        # 记录本次随机选中的槽位，方便存入 metadata
        selected_slots: Dict[str, str] = {}

        processed_base = base_tmpl
        # 简单的正则或字符串替换
        for slot, values in self.slots.items():
            if f"{{{slot}}}" in processed_base:
                val = random.choice(values)
                processed_base = processed_base.replace(f"{{{slot}}}", val)
                selected_slots[slot] = val

        modifier = random.choice(self.modifiers) if self.modifiers else ""
        full_scene = f"{processed_base}。{modifier}".strip()

        return {"description": full_scene, "slots": selected_slots}


class ScenarioFactory:
    def __init__(self, manager: ScenarioManager):
        self.manager = manager

    def produce(self) -> Dict[str, Any]:
        """对接 TaskRunner 的接口"""
        ctx = self.manager.get_random_context()
        return {
            "prompt": f"场景背景：【{ctx['description']}】。请创作剧本。",
            "world_info": ctx["description"],  # 存入 Conversation 模型
        }
