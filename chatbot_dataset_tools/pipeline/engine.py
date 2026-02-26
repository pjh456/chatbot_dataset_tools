import time

from typing import Optional
from .schema import PipelineConfig, StepConfig
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.datasets import DatasetLoader, ConcatDataset, Dataset
from chatbot_dataset_tools.registry import (
    transforms,
    filters,
    processors,
    sources,
    sinks,
)
from chatbot_dataset_tools.utils import (
    autodiscover_internal_components,
    import_module_from_string,
    get_logger,
)

logger = get_logger(__name__)


class PipelineEngine:
    def __init__(self, config_path_or_obj: str | PipelineConfig):
        if isinstance(config_path_or_obj, str):
            self.cfg = PipelineConfig.from_file(config_path_or_obj)
        else:
            self.cfg = config_path_or_obj

        self.current_dataset: Optional[Dataset] = None

        self._bootstrap_registry()

    def _bootstrap_registry(self):
        """初始化注册表：加载内部组件 + 外部插件"""

        # 1. 加载框架自带的组件 (ops, tasks, etc.)
        autodiscover_internal_components()

        # 2. 加载用户在 JSON 中定义的额外插件/脚本
        # 结构示例: "plugins": ["my_custom_script.py", "my_company.proprietary_ops"]
        plugins = getattr(self.cfg, "plugins", [])

        for plugin in plugins:
            try:
                # 如果是 .py 文件路径，甚至可以使用 importlib.util.spec_from_file_location 加载
                # 这里暂且假设用户传的是 Python 模块路径 (importable path)
                import_module_from_string(plugin)
                logger.info(f"Loaded plugin: {plugin}")
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin}': {e}")

    def run(self):
        logger.info(f"Starting Pipeline: {self.cfg.name}")

        if self.cfg.description:
            logger.info(f"Description: {self.cfg.description}")

        if self.cfg.variables:
            safe_vars = {
                k: (v if "key" not in k.lower() else "******")  # 保护密钥
                for k, v in self.cfg.variables.items()
            }
            logger.debug(f"Injected Variables: {safe_vars}")

        # === 核心逻辑：上下文融合 ===
        # 使用 config.switch 将 Pipeline JSON 中的 settings 应用到当前运行环境
        # 例如 JSON 中写了 "settings": { "proc": { "max_workers": 16 } }
        # 这里会自动生效，后续的 map/task 都会读到这个 16
        with config.switch(temporary_changes=self.cfg.settings):
            if self.cfg.settings:
                logger.info(
                    f"Applied temporary settings override: {list(self.cfg.settings.keys())}"
                )

            total_start = time.time()

            step = None
            try:
                for i, step in enumerate(self.cfg.steps):
                    step_start = time.time()
                    logger.info(
                        f"[Step {i+1}/{len(self.cfg.steps)}] Executing '{step.name}' ({step.type})"
                    )

                    self._execute_step(step)

                    elapsed = time.time() - step_start
                    logger.info(f"Step '{step.name}' completed in {elapsed:.2f}s")

            except Exception as e:
                logger.error(
                    f"Pipeline failed at step '{step.name if step else step}': {str(e)}",
                    exc_info=True,
                )
                raise e

        total_elapsed = time.time() - total_start
        logger.info(f"Pipeline Finished Successfully in {total_elapsed:.2f}s.")

    def _execute_step(self, step: StepConfig):
        debug_params = {
            k: v for k, v in step.params.items() if k not in ["inputs", "mapping"]
        }
        logger.debug(f"   Params: {debug_params}")

        # 动态分发
        handler_name = f"_handle_{step.type}"
        handler = getattr(self, handler_name, None)

        if not handler:
            logger.error(f"Unknown step type: {step.type}")
            raise NotImplementedError(f"Step type '{step.type}' is not supported.")

        handler(step)

    # --- Handlers ---

    def _handle_loader(self, step: StepConfig):
        inputs = step.params.get("inputs", [])
        loaded_datasets = []

        for inp in inputs:
            # 1. 提取 source_type (如 'file', 'http')
            src_type = inp.pop("source_type", "file")

            # 2. 从 Registry 获取类
            SourceCls = sources.get(src_type)

            # 3. 实例化 Source
            # 注意：这里的 **inp 包含了 path, format, encoding 等所有参数
            # 由于我们做了 ConfigContext，如果 inp 里缺省，FileSource 会自动去 GlobalSettings 里找
            source_instance = SourceCls(**inp)

            # 4. 加载
            ds = DatasetLoader.from_source(source_instance)
            loaded_datasets.append(ds)

        if not loaded_datasets:
            raise ValueError("Loader step has no inputs.")

        if len(loaded_datasets) > 1:
            self.current_dataset = ConcatDataset(loaded_datasets)
        else:
            self.current_dataset = loaded_datasets[0]

    def _handle_map(self, step: StepConfig):
        self._ensure_dataset(step)

        op_name = step.params.pop("op")
        transform_func = transforms.get(op_name)

        # 实例化闭包，例如 rename_roles(mapping={...})
        mapper = transform_func(**step.params)

        self.current_dataset = self.current_dataset.map(mapper)  # type: ignore

    def _handle_filter(self, step: StepConfig):
        self._ensure_dataset(step)

        op_name = step.params.pop("op")
        filter_func = filters.get(op_name)

        predicate = filter_func(**step.params)

        self.current_dataset = self.current_dataset.filter(predicate)  # type: ignore

    def _handle_task(self, step: StepConfig):
        self._ensure_dataset(step)

        proc_name = step.params.pop("processor")
        ProcessorCls = processors.get(proc_name)

        # 提取 TaskConfig 相关的参数 (并发数等)，其余留给 Processor
        # 这里做一个简单的参数分离（实际上 TaskRunner 会通过 GlobalSettings 获取默认值）
        task_overrides = {}
        for key in ["max_workers", "rate_limit", "ordered_results"]:
            if key in step.params:
                task_overrides[key] = step.params.pop(key)

        # 实例化处理器
        proc_instance = ProcessorCls(**step.params)

        # 运行
        self.current_dataset = self.current_dataset.run_task(  # type: ignore
            proc_instance, **task_overrides
        )

    def _handle_saver(self, step: StepConfig):
        self._ensure_dataset(step)

        sink_type = step.params.pop("sink_type", "file")
        SinkCls = sinks.get(sink_type)

        sink_instance = SinkCls(**step.params)

        # 执行保存 (触发计算)
        self.current_dataset.save_to(sink_instance)  # type: ignore

    def _ensure_dataset(self, step):
        if self.current_dataset is None:
            raise RuntimeError(
                f"Step '{step.name}' cannot run because no dataset is loaded. Did you forget a 'loader' step?"
            )
