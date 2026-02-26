from typing import Callable, Dict, Optional, List, TypeVar, Generic

T = TypeVar("T")


class Registry(Generic[T]):
    """
    通用注册表容器。
    用于管理 JSON 配置字符串到 Python 类/函数的映射。
    """

    def __init__(self, name: str, suffix_hint: Optional[str] = None):
        """
        Args:
            name: 注册表名称
            suffix_hint: 智能匹配后缀。例如 "Source"，当用户查找 "file" 时，会自动尝试 "FileSource"
        """
        self._name = name
        self._suffix_hint = suffix_hint
        self._registry: Dict[str, T] = {}

    def register(self, name: Optional[str] = None) -> Callable[[T], T]:
        """
        装饰器：注册一个对象。
        :param name: 注册名（JSON 中引用的名字）。如果不传，默认使用类名或函数名。
        """

        def decorator(obj: T) -> T:
            # 获取注册键名
            obj_name = name or getattr(obj, "__name__", None)

            if not obj_name or obj_name == "<lambda>":
                raise ValueError(
                    "Registered object must have a valid name or provide one explicitly"
                )

            # 检查重复
            if obj_name in self._registry:
                # TODO: 使用 logger.warning
                pass

            self._registry[obj_name] = obj
            return obj

        return decorator

    def get(self, name: str) -> T:
        """
        获取组件，支持智能模糊匹配。
        匹配优先级：
        1. 精确匹配 ("FileSource")
        2. 忽略大小写匹配 ("filesource")
        3. 拼接后缀后匹配 ("file" -> "FileSource")
        4. 拼接后缀且忽略大小写/下划线 ("file_source" -> "FileSource")
        """
        # 1. 尝试精确匹配
        if name in self._registry:
            return self._registry[name]

        # 准备候选项字典：将所有已注册的 key 转为 "小写无下划线" -> "原 key" 的映射
        # 例如: {'filesource': 'FileSource', 'httpsource': 'HTTPSource'}
        # 注意：这可以在 __init__ 里缓存，但为了代码简单这里实时计算（注册表通常不大）
        normalized_map = {self._normalize(k): k for k in self._registry.keys()}

        # 2. 尝试标准归一化匹配 (用户输入 "FileSource" 或 "filesource")
        query_norm = self._normalize(name)
        if query_norm in normalized_map:
            real_key = normalized_map[query_norm]
            return self._registry[real_key]

        # 3. 尝试拼接后缀匹配 (用户输入 "file", suffix="Source" -> 找 "filesource")
        if self._suffix_hint:
            # 拼接后缀
            hinted_name = name + self._suffix_hint
            hinted_norm = self._normalize(hinted_name)

            if hinted_norm in normalized_map:
                real_key = normalized_map[hinted_norm]
                return self._registry[real_key]

        # 4. 找不到
        raise ValueError(
            f"'{name}' not found in {self._name} registry. "
            f"Available: {list(self._registry.keys())}"
        )

    def _normalize(self, s: str) -> str:
        """移除下划线并转小写"""
        return s.lower().replace("_", "")

    def list_available(self) -> List[str]:
        """列出当前已注册的所有名称"""
        return sorted(list(self._registry.keys()))

    def __contains__(self, key: str) -> bool:
        return key in self._registry

    def __repr__(self) -> str:
        return f"<Registry {self._name}: {len(self._registry)} items>"
