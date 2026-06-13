from app.schemas.workflow import ViralPatternInput, ViralPatternOutput
from app.services.pattern_service import analyze_patterns


class ViralPatternAgent:
    name = "ViralPatternAgent"

    def run(self, agent_input: ViralPatternInput) -> ViralPatternOutput:
        patterns = analyze_patterns(category=agent_input.category)
        references: list[str] = []
        if patterns.frequent_title_keywords:
            keywords = "、".join(item.value for item in patterns.frequent_title_keywords[:5])
            references.append(f"标题高频词集中在：{keywords}。")
        if patterns.frequent_tags:
            tags = "、".join(item.value for item in patterns.frequent_tags[:5])
            references.append(f"标签高频方向包括：{tags}。")
        active_structures = [item.name for item in patterns.title_structures if item.count > 0][:3]
        if active_structures:
            references.append(f"常见标题结构：{'、'.join(active_structures)}。")
        if patterns.insufficient_sample_warning:
            references.append(patterns.insufficient_sample_warning)
        return ViralPatternOutput(patterns=patterns, references=references)
