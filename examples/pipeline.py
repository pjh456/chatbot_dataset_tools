import os


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_PATH, "sharegpt_example2.jsonl")
OUTPUT_ALPACA = os.path.join(BASE_PATH, "output_alpaca.json")

from chatbot_dataset_tools.core import (
    Dataset,
)
from chatbot_dataset_tools.adapters import ShareGPTAdapter, AlpacaAdapter
from chatbot_dataset_tools.io import DatasetReader, DatasetWriter
from chatbot_dataset_tools.transforms import ExtractorPresets
from chatbot_dataset_tools.renderers import RolePlayRenderer


def run_test():
    # 1. 初始化：使用 ShareGPT 加载原始数据
    # 设定输出时的渲染风格为星号动作和括号思考
    renderer = RolePlayRenderer(
        thought_prefix="[内心: ",
        thought_suffix="] ",
        action_prefix="<动作: ",
        action_suffix="> ",
    )

    sg_adapter = ShareGPTAdapter()
    reader = DatasetReader(adapter=sg_adapter)

    print("--- 步骤 1: 加载原始数据 ---")
    raw_ds = Dataset(list(reader.stream(INPUT_FILE)))
    print(f"加载成功，初始统计: {raw_ds.summary()}\n")

    # 2. 变换：提取动作和思考
    print("--- 步骤 2: 提取 Action 和 Thought ---")
    processed_ds = raw_ds.apply(ExtractorPresets.roleplay_standard())

    # 验证第一条数据的提取情况
    first_msg = processed_ds[0].messages[1]
    print(f"示例提取 - Thought: {first_msg.thought}")
    print(f"示例提取 - Action: {first_msg.action}")
    print(f"示例提取 - Content: {first_msg.content}\n")

    # 3. 过滤：只保留包含“动作”或“多轮”的对话
    print("--- 步骤 3: 过滤数据 ---")
    # 只要对话中任何一条消息有 action，或者对话超过 2 轮就保留
    filtered_ds = processed_ds.filter(
        lambda c: any(m.action for m in c.messages) or len(c.messages) > 2
    )
    print(f"过滤后剩余: {len(filtered_ds)} 条 (原 {len(raw_ds)} 条)\n")

    # 4. 统计摘要
    print("--- 步骤 4: 数据集统计摘要 ---")
    summary = filtered_ds.summary()
    for k, v in summary.items():
        print(f"{k}: {v}")
    print("")

    # 5. 转换并写入：转为 Alpaca 格式 (带 History)
    print("--- 步骤 5: 转换为 Alpaca 格式并写入 ---")
    # 这里我们注入自定义的 renderer，看看输出会不会变
    alpaca_adapter = AlpacaAdapter(renderer=renderer, use_history=True)
    writer = DatasetWriter(adapter=alpaca_adapter)

    writer.write(filtered_ds, OUTPUT_ALPACA, format="json")
    print(f"已成功写入至: {OUTPUT_ALPACA}")


if __name__ == "__main__":
    run_test()
