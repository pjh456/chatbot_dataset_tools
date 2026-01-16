import json
from typing import Iterable, Union
from pathlib import Path
from chatbot_dataset_tools.core import Conversation, BaseAdapter


class DatasetWriter:
    """数据集写入器。"""

    def __init__(self, adapter: BaseAdapter):
        """
        Args:
            adapter: 必须提供适配器，用于将 Conversation 转换回目标格式。
        """
        self.adapter = adapter

    def write(
        self,
        conversations: Iterable[Conversation],
        file_path: Union[str, Path],
        format: str = "jsonl",
    ):
        """将对话列表写入文件。

        Args:
            conversations: 对话模型迭代器（可以是生成器）。
            file_path: 输出路径。
            format: "json" 或 "jsonl"。
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 转换回原始字典格式
        raw_data = self.adapter.dump(list(conversations))

        if format.lower() == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                for item in raw_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
