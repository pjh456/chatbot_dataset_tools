from typing import Callable, Dict, Optional, List, TypeVar, Generic

T = TypeVar("T")


class Registry(Generic[T]):
    """
    通用注册表容器。
    用于管理 JSON 配置字符串到 Python 类/函数的映射。
    """

    def __init__(self, name: str) -> None:
        self._name = name
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
        根据名字获取已注册的对象。
        """
        if name not in self._registry:
            raise ValueError(
                f"'{name}' not found in {self._name} registry. "
                f"Available: {list(self._registry.keys())}"
            )
        return self._registry[name]

    def list_available(self) -> List[str]:
        """列出当前已注册的所有名称"""
        return sorted(list(self._registry.keys()))

    def __contains__(self, key: str) -> bool:
        return key in self._registry

    def __repr__(self) -> str:
        return f"<Registry {self._name}: {len(self._registry)} items>"
