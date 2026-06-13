from app.schemas.workflow import TagAndCoverInput, TagAndCoverOutput


class TagAndCoverAgent:
    name = "TagAndCoverAgent"

    def run(self, agent_input: TagAndCoverInput) -> TagAndCoverOutput:
        payload = agent_input.payload
        tags = list(
            dict.fromkeys(
                payload.tags
                + agent_input.similar_tags
                + [payload.category, payload.target_audience, payload.goal, "经验分享", "发布前检查", "内容优化"]
            )
        )[:8]
        return TagAndCoverOutput(
            recommended_tags=tags,
            cover_text=[
                payload.cover_text or f"{payload.category}发布前检查",
                f"{payload.target_audience}先看",
                "3 个关键判断",
            ],
            first_comment="你现在最纠结标题、开头还是正文结构？可以在评论区说说你的真实情况。",
            publish_time_suggestion="建议结合目标读者更容易浏览内容的时段做发布前复盘，不承诺具体流量表现。",
        )
