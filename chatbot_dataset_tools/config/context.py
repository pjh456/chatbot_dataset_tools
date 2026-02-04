from uuid import uuid4
from typing import Optional, Dict, Any, Type, cast
from .schema import APIConfig, ProcessingConfig, DatasetDefaults, GlobalSettings
from dataclasses import replace, fields, is_dataclass


class ConfigContext:
    def __init__(
        self, settings: GlobalSettings, name: str = "default", uid: Optional[str] = None
    ):
        self.uid = uid or str(uuid4())
        self.name = name
        self.settings = settings

    def clone(self, name: Optional[str] = None, **changes) -> "ConfigContext":
        """
        深度克隆并产生一个新的上下文。
        支持平铺参数 (role_map=...) 或 嵌套参数 (ds={"role_map": ...})。
        自动根据 GlobalSettings 的结构分发参数。
        """

        # 扫描 GlobalSettings，构建 字段名 -> 子配置类 的映射
        # 结果类似于: {'api': APIConfig, 'ds': DatasetDefaults, ...}
        section_map: Dict[str, Type] = {}
        # 构建 内部属性名 -> 所属 Section 的映射 (用于平铺参数查找)
        # 结果类似于: {'ollama_base_url': 'api', 'role_map': 'ds', ...}
        field_to_section: Dict[str, str] = {}

        for f in fields(GlobalSettings):
            if is_dataclass(f.type):
                ftype: Any = f.type
                section_map[f.name] = ftype
                for sub_f in fields(cast(Type, ftype)):
                    field_to_section[sub_f.name] = f.name

        # 准备更新容器
        updates_by_section: Dict[str, Dict[str, Any]] = {
            name: {} for name in section_map
        }
        root_updates: Dict[str, Any] = {}

        for key, value in changes.items():
            if key in section_map:
                # 嵌套更新，如 ds={"role_map": {...}}
                if isinstance(value, dict):
                    updates_by_section[key].update(value)
                else:
                    # 如果传的不是 dict 而是整个对象，直接替换
                    # TODO: 更详细的类型检查
                    root_updates[key] = value
            elif key in field_to_section:
                # 平铺更新，如 role_map={...}
                section = field_to_section[key]
                updates_by_section[section][key] = value
            else:
                # 根属性更新，如 extra={...}
                root_updates[key] = value

        # 执行替换逻辑
        final_params = {}
        for section_name in section_map:
            if section_name in root_updates:
                # 已经被整个对象替换了，跳过增量更新
                final_params[section_name] = root_updates.pop(section_name)
            elif updates_by_section[section_name]:
                # 增量更新子 Dataclass
                current_sub_obj = getattr(self.settings, section_name)
                final_params[section_name] = replace(
                    current_sub_obj, **updates_by_section[section_name]
                )

        # 合并剩余的根属性（如 extra 或未来的非 dataclass 字段）
        final_params.update(root_updates)
        new_settings = replace(self.settings, **final_params)
        return ConfigContext(new_settings, name=name or self.name)

    def __repr__(self):
        return f"<ConfigContext name={self.name} uid={self.uid[:8]}>"
