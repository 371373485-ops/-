from dataclasses import dataclass
from typing import Literal

from app.schemas.diagnosis import RiskEvidenceItem, RiskItem
from app.schemas.workflow import RiskReviewInput, RiskReviewOutput


Severity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class RiskRule:
    risk_type: str
    terms: tuple[str, ...]
    reason: str
    severity: Severity
    suggested_rewrite: str


RISK_RULES = (
    RiskRule(
        risk_type="绝对化表达",
        terms=("绝对", "保证", "百分百", "一定能", "任何人", "所有人", "永久有效", "全网最好", "必看", "必买"),
        reason="绝对化措辞会把个人经验包装成确定结论，容易造成夸大宣传或误导。",
        severity="medium",
        suggested_rewrite="改为“在我的场景里有参考价值”“适合部分情况参考”，并补充适用边界。",
    ),
    RiskRule(
        risk_type="夸大功效",
        terms=("立刻见效", "马上变好", "包治", "根治", "逆袭", "一招解决", "快速爆火"),
        reason="功效或结果表达过强，缺少条件、过程和个体差异说明。",
        severity="high",
        suggested_rewrite="改为描述真实观察和限制条件，例如“我观察到的变化是...，不同情况可能不同”。",
    ),
    RiskRule(
        risk_type="收益或增长承诺",
        terms=("稳赚", "保证变现", "保证涨粉", "必涨粉", "月入", "躺赚", "翻倍收益", "7天涨粉"),
        reason="收益、涨粉或变现结果不能承诺，尤其缺少真实可核验证据时风险较高。",
        severity="high",
        suggested_rewrite="改为经验分享或案例复盘，不承诺涨粉、变现或收益结果。",
    ),
    RiskRule(
        risk_type="医疗健康风险",
        terms=("治好", "治愈", "疗效", "药到病除", "替代医生", "诊断", "处方", "根治"),
        reason="医疗健康内容不能给出诊断、治疗或替代医生建议。",
        severity="high",
        suggested_rewrite="改为健康经验分享，并提示就医、咨询专业人士和个体差异。",
    ),
    RiskRule(
        risk_type="金融理财风险",
        terms=("保本", "无风险", "内幕", "荐股", "买入信号", "收益翻倍", "贷款套现"),
        reason="金融理财内容不能承诺收益、暗示无风险或提供确定买卖建议。",
        severity="high",
        suggested_rewrite="改为个人学习记录或风险提示，不提供买卖建议，不承诺收益。",
    ),
    RiskRule(
        risk_type="站外引流",
        terms=("加微信", "加我微信", "私信领取", "私信领", "私信发", "进群", "扫码", "站外", "VX", "v信", "公众号领取"),
        reason="诱导站外联系或领取资料可能违反平台规则，也可能涉及隐私信息收集。",
        severity="high",
        suggested_rewrite="改为站内评论区互动，例如“可以在评论区说说你的情况”。",
    ),
    RiskRule(
        risk_type="诱导互动",
        terms=("不点赞就", "必须收藏", "点赞抽奖", "评论抽奖", "转发领取", "关注后领取", "刷屏"),
        reason="强迫、诱导或利益交换式互动会影响合规和用户信任。",
        severity="medium",
        suggested_rewrite="改为开放式问题，不设置利益交换或强迫互动。",
    ),
    RiskRule(
        risk_type="虚假背书",
        terms=("官方认证", "专家推荐", "医生推荐", "全网第一", "销量第一", "万人验证", "平台认证"),
        reason="身份、数据、案例或第三方背书必须可证明；原文未提供证据时不能使用。",
        severity="high",
        suggested_rewrite="删除未证实背书，改为“这是我的个人经验/整理，不代表专业结论”。",
    ),
    RiskRule(
        risk_type="侵权或照搬风险",
        terms=("转载", "搬运", "同款文案", "照抄", "复制原文"),
        reason="复制、搬运或照抄他人内容可能涉及侵权，也不符合自有或授权样本的使用边界。",
        severity="medium",
        suggested_rewrite="仅借鉴结构和表达思路，使用自己的真实经历、场景和语言重新创作。",
    ),
)


RISK_RULES = RISK_RULES + (
    RiskRule(
        risk_type="绝对化表达",
        terms=("绝对", "保证", "百分百", "一定能", "任何人", "所有人", "永久有效", "全网最好", "必看", "必买"),
        reason="绝对化措辞会把个人经验包装成确定结论，容易造成夸大宣传或误导。",
        severity="medium",
        suggested_rewrite="改为经验分享、适用场景或边界说明，不承诺确定结果。",
    ),
    RiskRule(
        risk_type="夸大功效",
        terms=("立刻见效", "马上变好", "包治", "根治", "逆袭", "一招解决", "快速爆火"),
        reason="功效或结果表达过强，缺少条件、过程和个体差异说明。",
        severity="high",
        suggested_rewrite="改为描述真实观察和限制条件，提示不同情况可能不同。",
    ),
    RiskRule(
        risk_type="收益或增长承诺",
        terms=("稳赚", "保证变现", "保证涨粉", "必涨粉", "月入", "躺赚", "翻倍收益", "7天涨粉10万", "7天涨粉"),
        reason="收益、涨粉或变现结果不能承诺，尤其缺少真实可核验证据时风险较高。",
        severity="high",
        suggested_rewrite="改为经验分享或案例复盘，不承诺涨粉、变现或收益结果。",
    ),
    RiskRule(
        risk_type="站外引流",
        terms=("加微信", "加我微信", "私信领取", "私信领", "私信发", "进群", "扫码", "站外", "VX", "v信", "公众号领取"),
        reason="诱导站外联系或领取资料可能违反平台规则，也可能涉及隐私信息收集。",
        severity="high",
        suggested_rewrite="改为站内评论区互动，例如“可以在评论区说说你的情况”。",
    ),
    RiskRule(
        risk_type="侵权或照搬风险",
        terms=("转载", "搬运", "同款文案", "照抄", "复制原文"),
        reason="复制、搬运或照抄他人内容可能涉及侵权，也不符合自有或授权样本的使用边界。",
        severity="medium",
        suggested_rewrite="仅借鉴结构和表达思路，使用自己的真实经历、场景和语言重新创作。",
    ),
)


class RiskReviewAgent:
    name = "RiskReviewAgent"

    def run(self, agent_input: RiskReviewInput) -> RiskReviewOutput:
        field_texts = {
            "title": agent_input.payload.title,
            "content": agent_input.payload.content,
            "cover_text": agent_input.payload.cover_text or "",
            "comment_guide": agent_input.payload.comment_guide or "",
            "rewritten_titles": "\n".join(agent_input.rewritten_titles),
            "optimized_body": agent_input.optimized_body,
        }

        risk_items = self._scan(field_texts)
        risk_items.extend(self._ai_disclosure_items(field_texts))
        risks = self._legacy_risks(risk_items)
        safe_alternatives = self._safe_alternatives(risk_items)
        revision_suggestions = self._revision_suggestions(risk_items, safe_alternatives)
        risk_level = self._risk_level(risk_items)
        human_review_required = risk_level == "high" or any(
            item.risk_type in {"医疗健康风险", "金融理财风险"} for item in risk_items
        )

        if not risks:
            risks = [RiskItem(level="low", message="未发现明显高风险表达，发布前仍建议人工复核。")]
            revision_suggestions.append("保持真实、克制表达，避免把个人经验包装成确定承诺。")
            safe_alternatives.append("基于我的真实场景，这些做法仅供参考，具体情况建议自行判断。")

        return RiskReviewOutput(
            risk_level=risk_level,
            risk_items=risk_items,
            safe_alternatives=safe_alternatives,
            human_review_required=human_review_required,
            risks=risks,
            revision_suggestions=list(dict.fromkeys(revision_suggestions)),
        )

    def _scan(self, field_texts: dict[str, str]) -> list[RiskEvidenceItem]:
        items: list[RiskEvidenceItem] = []
        for field, text in field_texts.items():
            if not text:
                continue
            for rule in RISK_RULES:
                for term in [term for term in rule.terms if term in text]:
                    items.append(
                        RiskEvidenceItem(
                            field=field,
                            triggered_text=term,
                            risk_type=rule.risk_type,
                            reason=rule.reason,
                            severity=rule.severity,
                            suggested_rewrite=rule.suggested_rewrite,
                        )
                    )
        return self._dedupe(items)

    def _legacy_risks(self, risk_items: list[RiskEvidenceItem]) -> list[RiskItem]:
        grouped: dict[str, list[str]] = {}
        level_by_type: dict[str, str] = {}
        for item in risk_items:
            if item.risk_type == "AI 生成内容披露提醒":
                continue
            grouped.setdefault(item.risk_type, []).append(item.triggered_text)
            level_by_type[item.risk_type] = self._max_level(level_by_type.get(item.risk_type, "low"), item.severity)
        return [
            RiskItem(level=level_by_type[risk_type], message=f"检测到{risk_type}：{', '.join(dict.fromkeys(terms))}。")
            for risk_type, terms in grouped.items()
        ]

    def _safe_alternatives(self, risk_items: list[RiskEvidenceItem]) -> list[str]:
        alternatives = [item.suggested_rewrite for item in risk_items]
        if any(item.severity == "high" for item in risk_items if item.risk_type != "AI 生成内容披露提醒"):
            alternatives.append("高风险内容只保留事实核查、适用边界和人工复核提醒，不继续生成营销化标题或转化话术。")
        return list(dict.fromkeys(alternatives))

    def _revision_suggestions(self, risk_items: list[RiskEvidenceItem], safe_alternatives: list[str]) -> list[str]:
        suggestions = ["不得替用户编造资质、效果、数据、身份背书或案例。"]
        if risk_items:
            suggestions.append("将风险表达改为经验分享、过程复盘或适用场景说明。")
        suggestions.extend(safe_alternatives)
        return suggestions

    def _risk_level(self, risk_items: list[RiskEvidenceItem]) -> str:
        non_disclosure = [item for item in risk_items if item.risk_type != "AI 生成内容披露提醒"]
        if any(item.severity == "high" for item in non_disclosure):
            return "high"
        if any(item.severity == "medium" for item in non_disclosure):
            return "medium"
        return "low"

    def _ai_disclosure_items(self, field_texts: dict[str, str]) -> list[RiskEvidenceItem]:
        generated_text = "\n".join(field_texts.values())
        if any(term in generated_text for term in ("AI生成", "AI 生成", "AI 辅助", "AI辅助")):
            return []
        return [
            RiskEvidenceItem(
                field="ai_disclosure_notice",
                triggered_text="AI 辅助生成内容未明确披露",
                risk_type="AI 生成内容披露提醒",
                reason="诊断和改写可能由 AI 辅助生成，发布前应由用户人工复核，并按平台或场景要求决定是否披露。",
                severity="low",
                suggested_rewrite="内部使用时保留人工复核；如平台或场景要求披露，可补充“本文经 AI 辅助整理，已人工核对”。",
            )
        ]

    def _max_level(self, current: str, candidate: str) -> str:
        rank = {"low": 0, "medium": 1, "high": 2}
        return candidate if rank[candidate] > rank[current] else current

    def _dedupe(self, items: list[RiskEvidenceItem]) -> list[RiskEvidenceItem]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[RiskEvidenceItem] = []
        for item in items:
            key = (item.field, item.triggered_text, item.risk_type)
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
