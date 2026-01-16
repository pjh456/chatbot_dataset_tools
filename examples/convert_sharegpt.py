import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_PATH, "sharegpt_example.json")

from chatbot_dataset_tools.adapters import ShareGPTAdapter
from chatbot_dataset_tools.transforms import ExtractorPresets
import json

# 1. 模拟原始 ShareGPT 数据
with open(JSON_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# 2. 初始化适配器和转换器
adapter = ShareGPTAdapter()
action_extractor = ExtractorPresets.roleplay_standard()

# 3. 加载数据 -> 结构化模型
conversations = adapter.load(raw_data)

# 4. 执行变换（解构数据）
conversations = [action_extractor.apply(conv) for conv in conversations]

# 验证一下
msg = conversations[0].messages[1]
print(f"Thought: {msg.thought}")  # 我该怎么回他呢？
print(f"Action: {msg.action}")  # 深吸一口气
print(f"Content: {msg.content}")  # 你好呀！

# 5. 再次导出（或者转成其他格式）
final_data = adapter.dump(conversations)
