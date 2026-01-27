from uuid import uuid4
from typing import Optional, Dict, Any
from .schema import APIConfig, ProcessingConfig, DatasetDefaults, GlobalSettings
from dataclasses import replace, fields


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
        """
        ds_updates: Dict[str, Any] = {}
        api_updates: Dict[str, Any] = {}
        proc_updates: Dict[str, Any] = {}
        root_updates: Dict[str, Any] = {}

        # 定义字段集合
        ds_fields = {f.name for f in fields(DatasetDefaults)}
        api_fields = {f.name for f in fields(APIConfig)}
        proc_fields = {f.name for f in fields(ProcessingConfig)}

        for key, value in changes.items():
            if key == "ds":
                if isinstance(value, dict):
                    ds_updates.update(value)
                else:
                    root_updates["ds"] = value
            elif key == "api":
                if isinstance(value, dict):
                    api_updates.update(value)
                else:
                    root_updates["api"] = value
            elif key == "proc":
                if isinstance(value, dict):
                    proc_updates.update(value)
                else:
                    root_updates["proc"] = value
            elif key in ds_fields:
                ds_updates[key] = value
            elif key in api_fields:
                api_updates[key] = value
            elif key in proc_fields:
                proc_updates[key] = value
            else:
                root_updates[key] = value

        # 构造最终参数
        final_params = {}

        # 只有在确实有更新时才执行 replace，确保 ds/api/proc 始终是对象
        if "ds" in root_updates:
            final_params["ds"] = root_updates.pop("ds")
        elif ds_updates:
            final_params["ds"] = replace(self.settings.ds, **ds_updates)

        if "api" in root_updates:
            final_params["api"] = root_updates.pop("api")
        elif api_updates:
            final_params["api"] = replace(self.settings.api, **api_updates)

        if "proc" in root_updates:
            final_params["proc"] = root_updates.pop("proc")
        elif proc_updates:
            final_params["proc"] = replace(self.settings.proc, **proc_updates)

        final_params.update(root_updates)
        new_settings = replace(self.settings, **final_params)
        return ConfigContext(new_settings, name=name or self.name)

    def __repr__(self):
        return f"<ConfigContext name={self.name} uid={self.uid[:8]}>"
