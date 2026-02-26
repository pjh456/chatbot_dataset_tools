from typing import Optional, Iterator, List
from itertools import chain
from .dataset import Dataset, T
from .lazy_dataset import LazyDataset
from chatbot_dataset_tools.config import ConfigContext
from chatbot_dataset_tools.utils import get_logger

logger = get_logger(__name__)


class ConcatDataset(LazyDataset[T]):
    """
    将多个 Dataset 串联成一个逻辑数据集。
    用于处理 split 的文件或混合不同来源的数据。
    """

    def __init__(self, datasets: List[Dataset[T]], ctx: Optional[ConfigContext] = None):
        # 默认使用第一个数据集的上下文，或者传入的上下文
        base_ctx = ctx or (datasets[0].ctx if datasets else None)

        # 记录合并数量
        logger.debug(f"Concatenating {len(datasets)} datasets.")

        # 构造一个生成器，依次迭代所有子数据集
        # 注意：这里使用 lambda 是为了延迟执行，确保每次迭代都能重新触发底层 dataset 的加载
        def _chain_loader() -> Iterator[T]:
            # 手动展开 chain，以便在切换时打日志
            for i, ds in enumerate(datasets):
                # 尝试获取一些标识信息，比如文件路径
                source_info = "Unknown Source"
                if hasattr(ds, "_loader") and hasattr(
                    ds._loader, "path"  # type: ignore
                ):  # FileSource
                    source_info = ds._loader.path  # type: ignore
                elif hasattr(ds, "_loader") and hasattr(
                    ds._loader, "url"  # type: ignore
                ):  # HTTPSource
                    source_info = ds._loader.url  # type: ignore

                logger.debug(
                    f"  -> [Concat {i+1}/{len(datasets)}] Switching to source: {source_info}"
                )

                yield from ds

        super().__init__(_chain_loader(), ctx=base_ctx)
        self._source_datasets = datasets

    def __len__(self) -> int:
        """尝试计算总长度 (如果所有子数据集都知道长度)"""
        total = 0
        for ds in self._source_datasets:
            try:
                total += len(ds)
            except (TypeError, NotImplementedError):
                # 只要有一个算不出来，整体就无法预知
                raise TypeError("ConcatDataset contains dataset with unknown length")
        return total
