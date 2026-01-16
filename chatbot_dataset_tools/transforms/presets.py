from .extraction_rule import ExtractionRule
from .extractor import RegexExtractorTransform


class ExtractorPresets:
    @staticmethod
    def roleplay_standard():
        """最常用的 RP 提取逻辑：*动作*(思考)."""
        return RegexExtractorTransform(
            rules=[
                ExtractionRule(
                    field="action",
                    regex=r"\*(.*?)\*",  # 匹配 *动作*
                    remove_from_content=True,
                ),
                ExtractionRule(
                    field="thought",
                    regex=r"[\(（](.*?)[\)）]",  # 匹配 (思考) 或 （思考）
                    remove_from_content=True,
                ),
            ]
        )

    @staticmethod
    def deepseek_thought():
        """提取类似 DeepSeek 的显式思考标签."""
        return RegexExtractorTransform(
            rules=[
                ExtractionRule(
                    field="thought",
                    regex=r"<thought>(.*?)</thought>",
                    remove_from_content=True,
                )
            ]
        )
