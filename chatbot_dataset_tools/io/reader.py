import json
from typing import Generator, Dict, Any, List, Optional, Union
from pathlib import Path
from chatbot_dataset_tools.core import Conversation, BaseAdapter


class DatasetReader:
    """数据集读取器，支持多种格式的流式读取。"""

    @staticmethod
    def read_jsonl(
        file_path: Union[str, Path],
    ) -> Generator[Dict[str, Any], None, None]:
        """流式读取 JSONL 文件。"""
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    @staticmethod
    def read_json(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """读取标准 JSON 文件（列表格式）。"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError(f"Expected a list of objects in {file_path}")
            return data

    def __init__(self, adapter: Optional[BaseAdapter] = None):
        """
        Args:
            adapter: 可选的适配器。如果提供，读取的数据将自动转换为 Conversation 对象。
        """
        self.adapter = adapter

    def stream(
        self, file_path: Union[str, Path]
    ) -> Generator[Conversation, None, None]:
        """流式读取并转换为中间模型。

        自动根据扩展名判断使用 json 还是 jsonl。
        """
        path = Path(file_path)

        # 获取原始数据迭代器
        if path.suffix.lower() == ".jsonl":
            raw_iter = self.read_jsonl(path)
        else:
            # 对于标准 JSON，我们也模拟成迭代器
            raw_iter = iter(self.read_json(path))

        for raw_item in raw_iter:
            if self.adapter:
                # 适配器通常处理列表，这里我们包装一下
                convs = self.adapter.load([raw_item])
                for conv in convs:
                    yield conv
            else:
                # 如果没有适配器，抛出错误或返回原始数据（根据需求定）
                raise ValueError("Adapter is required for streaming Conversations.")
