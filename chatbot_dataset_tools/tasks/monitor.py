import json
import os
from typing import Set


class CheckpointManager:
    def __init__(self, path: str):
        self.path = path
        self.processed_ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        if not os.path.exists(self.path):
            return set()

        with open(self.path, "r") as f:
            try:
                return set(json.load(f))
            except:
                return set()

    def save(self, uid: str) -> None:
        self.processed_ids.add(uid)
        # TODO: 从全量改为增量写
        with open(self.path, "w") as f:
            json.dump(list(self.processed_ids), f)

    def is_processed(self, uid: str) -> bool:
        return uid in self.processed_ids
