import logging
import sys
from typing import Optional

# 定义日志格式
# [时间] [级别] [模块名] 信息
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    全局日志初始化函数。应该在程序入口（CLI 或 Engine）调用一次。
    """
    handlers = []

    # 1. 控制台 Handler (标准输出)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    handlers.append(console_handler)

    # 2. 文件 Handler (可选)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        handlers.append(file_handler)

    # 3. 配置根 Logger
    # 注意：这里设置的是 root logger，所有子模块 logger = logging.getLogger(__name__) 都会继承
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True,  # 强制覆盖之前的配置，避免重复打印
    )

    # 4. 抑制一些第三方库的啰嗦日志 (可选)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """所有模块应该通过这个函数获取 logger，或者直接用 logging.getLogger(__name__)"""
    return logging.getLogger(name)
