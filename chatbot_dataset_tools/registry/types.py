from .core import Registry
from typing import Callable, Type


# =============================================================================
# 数据处理 (Data Processing)
# =============================================================================

# 用于 Dataset.map() 的转换函数 (functions)
# JSON 示例: { "type": "map", "op": "rename_roles", ... }
transforms = Registry[Callable]("transforms")
register_transform = transforms.register

# 用于 Dataset.filter() 的过滤函数 (functions)
# JSON 示例: { "type": "filter", "op": "min_turns", ... }
filters = Registry[Callable]("filters")
register_filter = filters.register

# 用于 TaskRunner 的重型处理器 (Classes)
# JSON 示例: { "type": "task", "processor": "LLMProcessor", ... }
processors = Registry[Type]("processors")
register_processor = processors.register


# =============================================================================
# IO 与 格式化 (IO & Formatting)
# =============================================================================

# 数据格式化器 (Classes: Formatter)
# JSON 示例: { "type": "loader", "format": "alpaca", ... }
formatters = Registry[Type]("formatters")
register_formatter = formatters.register

# 数据源 (Classes: DataSource)
# JSON 示例: { "source_type": "file", ... }
sources = Registry[Type]("sources")
register_source = sources.register

# 数据汇 (Classes: DataSink)
# JSON 示例: { "sink_type": "http", ... }
sinks = Registry[Type]("sinks")
register_sink = sinks.register
