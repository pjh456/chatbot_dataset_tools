import pytest
from chatbot_dataset_tools.registry.core import Registry
from chatbot_dataset_tools.registry import (
    transforms,
    filters,
    register_transform,
    register_filter,
)


# 1. 测试核心 Registry 类的逻辑
def test_registry_basic_logic():
    # 创建一个独立的测试注册表
    test_reg = Registry("test")

    # 测试函数注册 (默认名称)
    @test_reg.register()
    def my_func():
        return "hello"

    assert "my_func" in test_reg
    assert test_reg.get("my_func") == my_func
    assert test_reg.get("my_func")() == "hello"

    # 测试类注册 (自定义名称)
    @test_reg.register("cool_class")
    class MyClass:
        pass

    assert "cool_class" in test_reg
    assert "MyClass" not in test_reg
    assert test_reg.get("cool_class") == MyClass


def test_registry_list_available():
    reg = Registry("list_test")

    @reg.register("a")
    def func_a():
        pass

    @reg.register("b")
    def func_b():
        pass

    available = reg.list_available()
    assert available == ["a", "b"]


def test_registry_error_handling():
    reg = Registry("error_test")

    # 尝试获取不存在的项
    with pytest.raises(ValueError) as excinfo:
        reg.get("none_exist")
    assert "not found" in str(excinfo.value)

    # 尝试注册没有 __name__ 属性且不提供显式名称的对象 (如 lambda)
    # 虽然装饰器通常用于有名字的对象，但如果是匿名对象会报错
    with pytest.raises(ValueError):
        reg.register()(lambda x: x)


# 2. 测试 __init__.py 中导出的预定义注册表
def test_global_registries_isolation():
    """测试不同的全局注册表是相互隔离的"""

    # 清空当前测试环境下的注册表状态（如果是单例需要小心，这里 Registry 是实例化的）
    # 注意：在真实的 pytest 运行中，之前的测试可能会污染全局变量
    # 这里的 transforms 是从 registry 模块导入的实例

    @register_transform("op_1")
    def transform_op():
        pass

    @register_filter("filter_1")
    def filter_op():
        pass

    # 检查 transforms 里有 op_1，但没有 filter_1
    assert "op_1" in transforms
    assert "filter_1" not in transforms

    # 检查 filters 里有 filter_1，但没有 op_1
    assert "filter_1" in filters
    assert "op_1" not in filters


def test_registry_overwrite():
    """测试同名注册会覆盖（当前的实现逻辑）"""
    reg = Registry("overwrite")

    @reg.register("same_name")
    def first():
        return 1

    @reg.register("same_name")
    def second():
        return 2

    assert reg.get("same_name")() == 2


# 3. 模拟真实场景：类装饰器
def test_processor_registration():
    from chatbot_dataset_tools.registry import register_processor, processors

    @register_processor("llm_v1")
    class MockProcessor:
        def process(self, x):
            return x

    assert "llm_v1" in processors
    instance = processors.get("llm_v1")()
    assert instance.process("test") == "test"
