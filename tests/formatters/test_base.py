from chatbot_dataset_tools.formatters.base import FieldMapper, BaseFormatter
from chatbot_dataset_tools.types import Message, Conversation
from chatbot_dataset_tools.config import config

# ---------------------------------------------------------
# 1. 测试 FieldMapper (核心变量替换逻辑)
# ---------------------------------------------------------


def test_field_mapper_inject():
    template = "Role: ${role}, Content: ${content}"
    vars = {"role": "user", "content": "hello world"}

    # 测试标准注入
    result = FieldMapper.inject(template, vars)
    assert result == "Role: user, Content: hello world"

    # 测试部分变量缺失应保留原样
    result_partial = FieldMapper.inject(template, {"role": "admin"})
    assert "Role: admin" in result_partial


def test_field_mapper_extract():
    template = "Role: ${role}, Msg: ${content}"
    actual_str = "Role: assistant, Msg: How can I help?"

    # 测试从字符串提取变量
    data = FieldMapper.extract(template, actual_str)
    assert data["role"] == "assistant"
    assert data["content"] == "How can I help?"

    # 测试不匹配的情况
    bad_str = "Something else entirely"
    assert FieldMapper.extract(template, bad_str) == {}


# ---------------------------------------------------------
# 2. 测试 BaseFormatter (角色映射逻辑)
# ---------------------------------------------------------


class DynamicTestFormatter(BaseFormatter):
    def format(self, conv: Conversation) -> list:
        return [
            f"{self.role_map.get(m.role, m.role)}: {m.content}" for m in conv.messages
        ]

    def parse(self, data: list) -> Conversation:
        msgs = []
        rev = self._get_reverse_role_map()
        for s in data:
            role_part, content = s.split(": ", 1)
            role_part = str(role_part)
            msgs.append(Message(rev.get(role_part, role_part), content))
        return Conversation(msgs)


def test_base_formatter_priority():
    """测试优先级：显式参数 > 全局配置"""
    conv = Conversation([Message("user", "hi")])

    # 1. 测试显式参数优先级最高
    fmt_explicit = DynamicTestFormatter(role_map={"user": "ExplicitUser"})
    with config.switch(ds={"role_map": {"user": "ConfigUser"}}):
        assert fmt_explicit.role_map["user"] == "ExplicitUser"
        assert "ExplicitUser: hi" in fmt_explicit.format(conv)

    # 2. 测试无参数时跟随全局配置
    fmt_config = DynamicTestFormatter()  # 不传 role_map
    with config.switch(ds={"role_map": {"user": "ConfigUser"}}):
        assert fmt_config.role_map["user"] == "ConfigUser"
        assert "ConfigUser: hi" in fmt_config.format(conv)


def test_reverse_role_map_dynamic():
    """测试反向映射是否随 role_map 动态更新"""
    fmt = DynamicTestFormatter()

    with config.switch(ds={"role_map": {"u": "1", "a": "2"}}):
        rev = fmt._get_reverse_role_map()
        assert rev == {"1": "u", "2": "a"}

    with config.switch(ds={"role_map": {"user": "human"}}):
        rev = fmt._get_reverse_role_map()
        assert rev == {"human": "user"}
