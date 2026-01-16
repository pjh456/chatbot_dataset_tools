from enum import Enum


class Role(str, Enum):
    """对话角色枚举.

    Attributes:
        SYSTEM: 系统指令，定义人格、规则或背景.
        USER: 用户输入.
        ASSISTANT: 模型输出.
        OBSERVER: 旁白/环境描述，通常用于描述非角色的第三方变动.
        TOOL: 外部工具调用的返回结果.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    OBSERVER = "observer"  # 旁白或环境变动
    TOOL = "tool"  # 预留给插件调用
