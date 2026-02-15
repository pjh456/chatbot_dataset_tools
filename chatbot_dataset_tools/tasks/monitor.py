import os
from typing import Set, List


class CheckpointManager:
    def __init__(self, path: str, interval: int = 10):
        self.path = path
        self.interval = interval
        self._buffer: List[str] = []
        # 使用 set 保证内存中查找 O(1)
        self.processed_ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        """从纯文本文件加载已处理的 ID，每行一个"""
        if not os.path.exists(self.path):
            return set()

        with open(self.path, "r", encoding="utf-8") as f:
            # 去除每行首尾空格及换行符
            return {line.strip() for line in f if line.strip()}

    def is_processed(self, uid: str) -> bool:
        return uid in self.processed_ids

    def save(self, uid: str):
        """记录进度（带缓冲的追加写入）"""
        if uid in self.processed_ids:
            return

        self.processed_ids.add(uid)
        self._buffer.append(uid)

        # 达到间隔后执行刷新
        if len(self._buffer) >= self.interval:
            self.flush()

    def flush(self):
        """强制将缓冲区内容追加到磁盘"""
        if not self._buffer:
            return

        # 追加写入，无需读取旧内容
        with open(self.path, "a", encoding="utf-8") as f:
            for uid in self._buffer:
                f.write(f"{uid}\n")

        self._buffer = []

    def __del__(self):
        """确保程序退出时，缓冲区内剩余的数据也能保存"""
        self.flush()
