import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from chatbot_dataset_tools.config import (
    config,
    ConfigContext,
    GlobalSettings,
    APIConfig,
    ProcessingConfig,
)


def test_config_singleton():
    """测试 ConfigManager 是否为全局单例"""
    from chatbot_dataset_tools.config import ConfigManager

    another_config = ConfigManager()
    assert config is another_config
    assert config.current.name == "default"


def test_context_registration_and_retrieval():
    """测试通过唯一标识符(UID)和名称(Name)检索上下文"""
    new_settings = GlobalSettings(api=APIConfig(openai_api_key="test-key"))
    new_ctx = ConfigContext(new_settings, name="test-env")

    # 注册
    config.register(new_ctx)

    # 通过名称检索
    config_from_name = config.get_context("test-env")
    assert config_from_name is not None
    assert config_from_name.settings.api.openai_api_key == "test-key"

    # 通过 UID 检索
    config_from_uid = config.get_context(new_ctx.uid)
    assert config_from_uid is not None
    assert config_from_uid.name == "test-env"


def test_context_switch_mechanism():
    """测试 switch 上下文切换及其自动恢复"""
    original_url = config.settings.api.ollama_base_url
    custom_url = "http://custom-server:11434"

    # 创建并注册一个新的上下文
    custom_settings = GlobalSettings(api=APIConfig(ollama_base_url=custom_url))
    custom_ctx = ConfigContext(custom_settings, name="custom-env")
    config.register(custom_ctx)

    # 1. 测试通过名称切换
    with config.switch("custom-env"):
        assert config.settings.api.ollama_base_url == custom_url
        assert config.current.name == "custom-env"

    # 退出后应恢复
    assert config.settings.api.ollama_base_url == original_url

    # 2. 测试临时属性覆盖 (Anonymous Switch)
    # 注意：replace 需要传入完整的子对象，或者在实现中支持深层 merge
    temp_api = APIConfig(ollama_base_url="http://temp-url")
    with config.switch(api=temp_api):
        assert config.settings.api.ollama_base_url == "http://temp-url"
        assert config.current.name == "_temp"
    assert config.settings.api.ollama_base_url != "http://temp-url"
    assert config.current.name != "_temp"


def test_nested_config_replacement():
    """测试深层配置对象的替换逻辑"""
    new_proc = ProcessingConfig(max_workers=99)
    with config.switch(proc=new_proc):
        assert config.settings.proc.max_workers == 99
        # api 配置应保持默认
        assert config.settings.api.ollama_base_url == "http://localhost:11434"


def test_concurrency_isolation():
    """
    核心测试：验证在多线程环境下配置是否相互隔离 (Thread Safety)
    这是 ConfigContext 设计的最重要指标。
    """

    def worker(worker_id: int, target_url: str):
        # 每个线程设置不同的配置
        temp_api = APIConfig(ollama_base_url=target_url)
        with config.switch(api=temp_api):
            # 在该线程内，配置应该是 target_url
            import time

            time.sleep(0.1)  # 增加并发冲突的可能性
            if config.settings.api.ollama_base_url != target_url:
                return False
        return True

    tasks = [
        (1, "http://server-1"),
        (2, "http://server-2"),
        (3, "http://server-3"),
        (4, "http://server-4"),
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda x: worker(*x), tasks))

    # 所有线程都应该看到自己私有的配置，互不干扰
    assert all(results) is True
    # 主线程配置依然保持默认
    assert config.settings.api.ollama_base_url == "http://localhost:11434"


def test_uid_uniqueness():
    """测试每个 Context 即使内容相同，UID 也应该是唯一的"""
    ctx1 = ConfigContext(GlobalSettings(), name="env1")
    ctx2 = ConfigContext(GlobalSettings(), name="env1")

    assert ctx1.uid != ctx2.uid
    assert ctx1.clone().uid != ctx1.uid
