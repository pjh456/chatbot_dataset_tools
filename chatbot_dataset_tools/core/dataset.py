import random
from typing import List, Callable, Optional, Union, Dict, Any, Iterator, Tuple
from .conversation import Conversation
from .transform import BaseTransform


class Dataset:
    """对话数据集容器，提供高级操作接口.

    Attributes:
        conversations (List[Conversation]): 存储所有对话模型的列表.
    """

    def __init__(self, conversations: Optional[List[Conversation]] = None):
        self.conversations = conversations or []

    def __len__(self) -> int:
        return len(self.conversations)

    def __getitem__(self, index: int) -> Conversation:
        return self.conversations[index]

    def __iter__(self) -> Iterator[Conversation]:
        return iter(self.conversations)

    def append(self, conversation: Conversation):
        self.conversations.append(conversation)

    def extend(self, other: Union["Dataset", List[Conversation]]):
        if isinstance(other, Dataset):
            self.conversations.extend(other.conversations)
        else:
            self.conversations.extend(other)

    def clone(self) -> "Dataset":
        """克隆整个数据集及其包含的所有对话."""
        return self.__class__([c.clone() for c in self.conversations])

    # --- 数据变换与清洗 ---

    def apply(self, transform: BaseTransform) -> "Dataset":
        """应用一个变换器到数据集的所有对话上.

        Args:
            transform: 实现了 apply 方法的变换器.

        Returns:
            Dataset: 变换后的新数据集对象.
        """
        new_convs = [transform.apply(c) for c in self.conversations]
        return self.__class__(new_convs)

    def filter(self, criteria: Callable[[Conversation], bool]) -> "Dataset":
        """过滤数据集.

        Args:
            criteria: 一个返回 bool 的函数。True 表示保留。

        示例:
            dataset.filter(lambda c: len(c.messages) > 2)
        """
        return self.__class__([c.clone() for c in self.conversations if criteria(c)])

    def map(self, func: Callable[[Conversation], Conversation]) -> "Dataset":
        """对每条对话应用自定义函数."""
        return self.__class__([func(c.clone()) for c in self.conversations])

    # --- 集合操作 ---

    def shuffle(self, seed: Optional[int] = None) -> "Dataset":
        """打乱数据集顺序."""
        new_convs = [c.clone() for c in self.conversations]
        if seed is not None:
            random.seed(seed)
        random.shuffle(new_convs)
        return self.__class__(new_convs)

    def split(self, ratio: float) -> Tuple["Dataset", "Dataset"]:
        """按比例切分为两个数据集（如训练集和测试集）.

        Args:
            ratio: 第一个数据集所占的比例 (0.0 ~ 1.0).
        """
        split_idx = int(len(self.conversations) * ratio)
        return (
            self.__class__(self.conversations[:split_idx]),
            self.__class__(self.conversations[split_idx:]),
        )

    # --- 统计与分析 ---

    def summary(self) -> Dict[str, Any]:
        """返回数据集的统计摘要."""
        total_convs = len(self.conversations)
        if total_convs == 0:
            return {"status": "Empty Dataset"}

        total_msgs = sum(len(c.messages) for c in self.conversations)
        avg_msgs = total_msgs / total_convs

        role_counts = {}
        for c in self.conversations:
            for m in c.messages:
                role_counts[m.role] = role_counts.get(m.role, 0) + 1

        return {
            "total_conversations": total_convs,
            "total_messages": total_msgs,
            "avg_messages_per_conv": round(avg_msgs, 2),
            "role_distribution": role_counts,
        }

    def __repr__(self) -> str:
        s = self.summary()
        return (
            f"<Dataset: {s['total_conversations']} convs, {s['total_messages']} msgs>"
        )
