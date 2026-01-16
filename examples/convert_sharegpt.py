from chatbot_dataset_tools.adapters import ShareGPTAdapter
from chatbot_dataset_tools.transforms import ExtractActionTransform

# 1. 模拟原始 ShareGPT 数据
raw_data = [
    {
        "id": "1",
        "conversations": [
            {"from": "human", "value": "你好"},
            {"from": "gpt", "value": "*微笑地看着你* 你也好呀。"},
        ],
    }
]

# 2. 初始化适配器和转换器
adapter = ShareGPTAdapter()
action_extractor = ExtractActionTransform()

# 3. 加载数据 -> 结构化模型
conversations = adapter.load(raw_data)

# 4. 执行变换（解构数据）
for conv in conversations:
    action_extractor.apply(conv)

# 验证一下
msg = conversations[0].messages[1]
print(f"Role: {msg.role}")
print(f"Action: {msg.action}")  # 应该是: 微笑地看着你
print(f"Content: {msg.content}")  # 应该是: 你也好呀。

# 5. 再次导出（或者转成其他格式）
final_data = adapter.dump(conversations)
