import os
import re
from typing import Any
from chatbot_dataset_tools.core import Conversation
from chatbot_dataset_tools.io import DatasetWriter


def setup_persistence(save_dir: str, adapter: Any):
    """创建持久化回调函数"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    writer = DatasetWriter(adapter=adapter)

    # 1. 自动计算起始编号
    existing_files = [f for f in os.listdir(save_dir) if f.startswith("raw_data")]
    indices = [
        int(re.findall(r"\d+", f)[0]) for f in existing_files if re.findall(r"\d+", f)
    ]
    start_idx = max(indices) + 1 if indices else 1

    # 2. 定义保存回调
    def on_success(conv: Conversation, idx: int):
        filename = os.path.join(save_dir, f"raw_data{idx}.json")
        # 将单个 Conversation 写入文件
        writer.write([conv], filename, format="json")

    return start_idx, on_success
