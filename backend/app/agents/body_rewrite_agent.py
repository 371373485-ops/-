from app.schemas.workflow import BodyRewriteInput, BodyRewriteOutput
from app.services.rewrite_explanation_service import append_missing_detail_placeholders


HIGH_RISK_TERMS = (
    "保证",
    "绝对",
    "任何人",
    "所有人",
    "快速爆火",
    "保证变现",
    "稳赚",
    "必涨粉",
    "加微信",
    "私信领取",
)


def _has_high_risk_claim(text: str) -> bool:
    return any(term in text for term in HIGH_RISK_TERMS) or (("7天" in text or "七天" in text) and "涨粉" in text)


class BodyRewriteAgent:
    name = "BodyRewriteAgent"

    def run(self, agent_input: BodyRewriteInput) -> BodyRewriteOutput:
        payload = agent_input.payload
        source_text = f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}\n{payload.comment_guide or ''}"

        if _has_high_risk_claim(source_text):
            optimized_body = (
                f"这篇内容面向{payload.target_audience}，主题是{payload.category}。\n\n"
                "先说结论：原文里存在绝对化、结果承诺或站外引流风险，建议改成经验复盘和发布前自查，不承诺流量、收益或确定效果。\n\n"
                "可以按这个结构重写：\n"
                "1. 先交代你的真实背景、内容阶段或复盘对象。\n"
                "2. 再拆出 2-3 个你认为有参考价值的判断点，只描述过程和观察。\n"
                "3. 最后补充适用边界，提醒不同账号、选题和执行条件下结果会有差异。\n\n"
                "建议使用“我的复盘是”“这几点对我有参考”“适合参考但不保证结果”等表达。"
            )
            notes = ["移除绝对化或结果承诺表达。", "改为经验复盘结构，不编造用户未提供的事实。"]
        else:
            optimized_body = (
                f"这篇内容写给{payload.target_audience}，主题是{payload.category}。\n\n"
                "先说结论：发布前不要只看文案是否顺，而要检查读者能不能马上看懂“适合谁、解决什么、凭什么信”。\n\n"
                "建议这样整理：\n"
                "1. 开头先点明读者和具体场景，让读者判断这篇是否与自己有关。\n"
                "2. 正文拆成 2-3 个关键判断点，每一点尽量配一个真实过程、条件或观察。\n"
                "3. 结尾补充适用边界和站内开放问题，方便读者评论自己的情况。\n\n"
                f"保留原始重点：{payload.content[:180]}"
            )
            notes = ["保留用户原意，不新增未经提供的事实。", "强化结论前置、步骤感和适用提醒。"]

        return BodyRewriteOutput(
            optimized_body=append_missing_detail_placeholders(optimized_body, payload),
            rewrite_notes=notes,
        )
