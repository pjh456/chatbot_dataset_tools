import re
from typing import List
from chatbot_dataset_tools.core import Conversation, BaseTransform
from .extraction_rule import ExtractionRule


class RegexExtractorTransform(BaseTransform):
    """基于正则表达式的内容提取器."""

    def __init__(self, rules: List[ExtractionRule]):
        self.rules = rules
        # 预编译正则提高效率
        self.compiled_rules = [
            (rule, re.compile(rule.regex, re.DOTALL)) for rule in rules
        ]

    def apply(self, conversation: Conversation) -> Conversation:
        # 使用之前定义的 clone 方法，确保非破坏性操作
        new_conv = conversation.clone()

        for msg in new_conv.messages:
            content = msg.content

            for rule, pattern in self.compiled_rules:
                # 1. 查找所有匹配项
                matches = pattern.findall(content)
                if not matches:
                    continue

                # 2. 将匹配到的内容存入对应字段
                # 注意：matches 可能是字符串列表，也可能是 tuple 列表（如果有多个分组）
                extracted_text = self._process_matches(matches, rule.join_str)

                # 动态设置字段 (thought, action, scene)
                current_val = getattr(msg, rule.field) or ""
                if current_val:
                    new_val = current_val + rule.join_str + extracted_text
                else:
                    new_val = extracted_text
                setattr(msg, rule.field, new_val)

                # 3. 如果需要，从原文中抹除
                if rule.remove_from_content:
                    content = pattern.sub("", content)

            # 最后更新清洗后的正文，并去掉多余空格
            msg.content = content.strip()

        return new_conv

    def _process_matches(self, matches: List, join_str: str) -> str:
        processed = []
        for m in matches:
            if isinstance(m, tuple):
                # 如果正则有多个分组，取第一个非空的
                text = next((item for item in m if item), "")
                processed.append(text.strip())
            else:
                processed.append(m.strip())
        return join_str.join(processed)
