from pydantic import BaseModel


class ExtractionRule(BaseModel):
    """提取规则配置.

    Attributes:
        field: 目标字段 (thought, action, scene).
        regex: 用于匹配的正则表达式（建议使用带括号的分组）.
        remove_from_content: 提取后是否从原 content 中删除该部分.
        join_str: 如果匹配到多项，用什么字符连接.
    """

    field: str
    regex: str
    remove_from_content: bool = True
    join_str: str = " "
