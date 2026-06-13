from app.schemas.workflow import TitleRewriteInput, TitleRewriteOutput


class TitleRewriteAgent:
    name = "TitleRewriteAgent"

    def run(self, agent_input: TitleRewriteInput) -> TitleRewriteOutput:
        payload = agent_input.payload
        category = payload.category
        audience = payload.target_audience
        return TitleRewriteOutput(
            strong_hook=f"{audience}发布前先看：{category}这 3 个问题最影响点击",
            save_worthy=f"{category}发布前检查清单：适合{audience}收藏复盘",
            contrast_conflict=f"{category}不是写得越满越好，关键是这几处先说清",
            beginner_friendly=f"{audience}也能用的{category}优化思路：从标题到评论区",
            workplace_version=f"发布前 5 分钟快速检查：这篇{category}还能怎么改",
        )
