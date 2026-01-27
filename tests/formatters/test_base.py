from chatbot_dataset_tools.formatters.base import FieldMapper, BaseFormatter
from chatbot_dataset_tools.types import Message, Conversation

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


# 定义一个最小化的具体实现类来测试基类
class SimpleTestFormatter(BaseFormatter):
    role_map = {"user": "Human", "assistant": "AI"}

    def format(self, conv: Conversation) -> list:
        # 简单的格式化逻辑：转成字符串列表
        res = []
        for m in conv.messages:
            mapped_role = self.role_map.get(m.role, m.role)
            res.append(f"{mapped_role}: {m.content}")
        return res

    def parse(self, data: list) -> Conversation:
        # 简单的解析逻辑
        msgs = []
        reverse_map = self._get_reverse_role_map()
        for s in data:
            # 假设格式是 "Role: Content"
            role_part, content = s.split(": ", 1)
            role_part = str(role_part)
            actual_role = reverse_map.get(role_part, role_part)
            msgs.append(Message(actual_role, content))
        return Conversation(msgs)


def test_base_formatter_role_mapping():
    formatter = SimpleTestFormatter()
    conv = Conversation([Message("user", "hi"), Message("assistant", "hello")])

    # 1. 测试 Format (正向角色映射)
    formatted = formatter.format(conv)
    assert formatted[0] == "Human: hi"
    assert formatted[1] == "AI: hello"

    # 2. 测试 Parse (反向角色映射)
    parsed_conv = formatter.parse(formatted)
    assert parsed_conv.messages[0].role == "user"
    assert parsed_conv.messages[1].role == "assistant"


def test_reverse_role_map_generation():
    class Dummy(BaseFormatter):
        role_map = {"a": "1", "b": "2"}

        def format(self, conv):
            return None

        def parse(self, data):
            return Conversation([])

    d = Dummy()
    rev = d._get_reverse_role_map()
    assert rev == {"1": "a", "2": "b"}
