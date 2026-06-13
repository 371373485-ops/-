from dataclasses import dataclass

from app.agents.evidence_based_diagnosis_agent import EvidenceBasedDiagnosisAgent
from app.agents.risk_review_agent import RiskReviewAgent
from app.agents.similar_case_agent import SimilarCaseAgent
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse, RewrittenVersions, RiskReviewSummary, ScoreItem
from app.schemas.workflow import RiskReviewInput
from app.services.evidence_workbench_service import (
    build_diagnosis_sources,
    build_evidence_diagnosis,
    build_reader_perspectives,
    build_revision_tasks,
    build_score_explanation,
    build_score_deductions,
)
from app.services.rewrite_explanation_service import append_missing_detail_placeholders, build_rewrite_explanations
from app.services.sample_insight_service import build_sample_insights


WEIGHTS = {
    "title_score": 0.15,
    "opening_score": 0.15,
    "structure_score": 0.15,
    "emotion_score": 0.10,
    "value_score": 0.15,
    "interaction_score": 0.10,
    "tag_score": 0.10,
    "style_score": 0.05,
    "conversion_score": 0.05,
}

PAIN_WORDS = ("痛点", "踩坑", "避坑", "不会", "问题", "失败", "焦虑", "纠结", "后悔")
VALUE_WORDS = ("清单", "方法", "步骤", "攻略", "提升", "改善", "搞懂", "模板", "检查", "复盘", "场景", "提效", "效率", "要点")
TRUST_WORDS = ("我", "真实", "亲测", "记录", "发现", "复盘", "对比", "过程", "核对", "确认", "来源")
ACTION_WORDS = ("评论", "评论区", "留言", "收藏", "你觉得", "你会", "你最想", "欢迎", "告诉我", "聊聊")
STYLE_WORDS = ("真实", "亲测", "避坑", "清单", "复盘", "普通人", "新手", "场景")
BOUNDARY_WORDS = ("适合", "不适合", "预算", "需求", "场景", "限制", "前提", "来源", "细节", "核对")


@dataclass
class RuleScore:
    key: str
    name: str
    score: int
    reason: str
    issues: list[str]
    suggestions: list[str]


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word and word in text for word in words)


def _first_paragraph(content: str) -> str:
    parts = [part.strip() for part in content.splitlines() if part.strip()]
    return parts[0] if parts else content[:80]


def _paragraph_count(content: str) -> int:
    return len([part for part in content.splitlines() if part.strip()])


def _audience_matched(text: str, target_audience: str) -> bool:
    compact_target = target_audience.replace("人群", "").replace("用户", "").replace("人", "")
    if target_audience and target_audience in text:
        return True
    if compact_target and compact_target in text:
        return True
    if "职场" in target_audience and any(alias in text for alias in ("职场", "办公", "周报", "会议", "资料", "上班")):
        return True
    if "护肤" in target_audience and "护肤" in text:
        return True
    if "新手" in target_audience and any(alias in text for alias in ("新手", "小白", "入门")):
        return True
    if "创作者" in target_audience and any(alias in text for alias in ("创作者", "内容", "发布", "笔记")):
        return True
    return False


def _score_title(payload: DiagnosisRequest) -> RuleScore:
    title = payload.title
    score = 45
    issues: list[str] = []
    suggestions: list[str] = []
    hits: list[str] = []

    if any(char.isdigit() for char in title):
        score += 12
        hits.append("数字")
    else:
        issues.append("标题缺少数字或明确数量，信息抓手偏弱。")
        suggestions.append("可以加入“3 个检查点”“5 分钟自查”等具体数量。")

    if _contains_any(title, PAIN_WORDS):
        score += 12
        hits.append("痛点")
    elif _contains_any(title, VALUE_WORDS):
        score += 8
        hits.append("价值")
    else:
        issues.append("标题痛点不够明显。")
        suggestions.append("补充目标人群最关心的场景或发布前阻碍。")

    if _contains_any(title, VALUE_WORDS):
        score += 12
        if "价值" not in hits:
            hits.append("价值")
    else:
        suggestions.append("标题可以增加清单、方法、检查、复盘等收益词。")

    if _audience_matched(title, payload.target_audience):
        score += 11
        hits.append("具体对象")
    else:
        issues.append("标题没有明确具体对象。")
        suggestions.append(f"建议点名目标人群，例如“{payload.target_audience}”。")

    if 8 <= len(title) <= 36:
        score += 10
    else:
        issues.append("标题长度不在推荐区间，可能影响阅读效率。")

    reason = f"标题命中：{', '.join(hits) if hits else '暂无明显信息抓手'}。"
    return RuleScore("title_score", "标题吸引力", _clamp(score), reason, issues, suggestions)


def _score_opening(payload: DiagnosisRequest) -> RuleScore:
    opening = _first_paragraph(payload.content)
    score = 45
    issues: list[str] = []
    suggestions: list[str] = []

    if len(opening) <= 120:
        score += 12
    else:
        issues.append("开头偏长，进入主题较慢。")
        suggestions.append("开头控制在 2-3 句内，先给结论或冲突。")

    if _audience_matched(opening, payload.target_audience):
        score += 12
    else:
        issues.append("开头没有快速点名目标人群。")
        suggestions.append("第一段直接写明这篇适合谁。")

    if _contains_any(opening, PAIN_WORDS + VALUE_WORDS + ("先说结论", "关键", "适合")):
        score += 18
    else:
        issues.append("开头缺少痛点或收益承诺。")
        suggestions.append("用“先说结论”“发布前先检查”等方式提高留存。")

    if _contains_any(opening, TRUST_WORDS) or _contains_any(payload.content, ("核对", "确认", "来源")):
        score += 13
    else:
        suggestions.append("加入真实经历或个人复盘视角，让开头更可信。")

    return RuleScore("opening_score", "开头留存力", _clamp(score), "根据开头长度、人群、痛点收益和真实感评分。", issues, suggestions)


def _score_structure(payload: DiagnosisRequest) -> RuleScore:
    content = payload.content
    paragraphs = _paragraph_count(content)
    has_list = _contains_any(content, ("1.", "2.", "①", "②", "第一", "第二", "- "))
    score = (
        42
        + (18 if paragraphs >= 3 else 0)
        + (18 if has_list else 0)
        + (10 if len(content) >= 180 else 0)
        + (10 if paragraphs >= 3 and has_list else 0)
    )
    issues = []
    suggestions = []
    if paragraphs < 3:
        issues.append("正文分段不足，阅读层次不够清晰。")
        suggestions.append("拆成 3-5 个短段，每段只表达一个重点。")
    if not has_list:
        issues.append("正文缺少清单或步骤结构。")
        suggestions.append("加入编号、清单或步骤，让用户更容易收藏。")
    if len(content) < 120:
        issues.append("正文信息量偏少。")
        suggestions.append("补充真实场景、判断步骤、对比依据和限制条件。")
    return RuleScore("structure_score", "内容结构", _clamp(score), f"检测到 {paragraphs} 个有效段落。", issues, suggestions)


def _score_keyword_dimension(key: str, name: str, text: str, words: tuple[str, ...], base: int, per_hit: int, missing_issue: str, suggestion: str) -> RuleScore:
    hits = [word for word in words if word in text]
    return RuleScore(
        key,
        name,
        _clamp(base + len(hits) * per_hit),
        f"命中关键词：{', '.join(hits) if hits else '暂无'}。",
        [] if hits else [missing_issue],
        [] if hits else [suggestion],
    )


def _score_tags(payload: DiagnosisRequest) -> RuleScore:
    tags = payload.tags
    joined = " ".join(tags)
    score = 45 + (18 if len(tags) >= 3 else 0) + (14 if payload.category in joined else 0)
    issues = []
    suggestions = []
    if len(tags) < 3:
        issues.append("标签数量偏少。")
        suggestions.append("至少覆盖赛道、人群、内容形式三个方向。")
    if payload.category not in joined:
        issues.append("标签没有覆盖内容赛道。")
        suggestions.append(f"补充赛道标签：{payload.category}。")
    if payload.goal in joined or _contains_any(joined, ("经验", "清单", "攻略", "复盘", "检查", "收藏")):
        score += 13
    else:
        suggestions.append("补充内容形式标签，例如 #发布前检查 #经验复盘。")
    return RuleScore("tag_score", "标签匹配", _clamp(score), f"当前提供 {len(tags)} 个标签。", issues, suggestions)


def _score_conversion(payload: DiagnosisRequest) -> RuleScore:
    text = f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}"
    result = _score_keyword_dimension(
        "conversion_score",
        "转化判断",
        text,
        BOUNDARY_WORDS,
        45,
        9,
        "内容中缺少适用场景、选择依据或转化判断。",
        "补充“适合谁”“为什么选”“怎么判断是否需要”等信息。",
    )
    if payload.goal in ("引流", "转化") and not _contains_any(text, ("评论", "留言", "了解", "选择")):
        result.issues.append("发布目标偏转化，但结尾承接动作不够明确。")
        result.suggestions.append("使用合规的站内评论引导，避免诱导站外引流。")
        result.score = max(0, result.score - 8)
    return result


def _optimized_body(payload: DiagnosisRequest) -> str:
    return (
        f"这篇内容整理给{payload.target_audience}，主题是{payload.category}。\n\n"
        "先说结论：发布前最值得检查的不是文案是否“看起来高级”，而是读者能否快速看懂适合谁、解决什么、凭什么相信。\n\n"
        "可以这样拆：\n"
        "1. 开头先说明具体场景和读者状态，让读者判断自己是不是同一类情况。\n"
        "2. 正文给出 2-3 个判断点，每一点都尽量配真实过程、条件或观察。\n"
        "3. 结尾补充适用提醒，不把个人经验说成绝对结论。\n\n"
        "如果你也在做类似内容，可以先从自己的真实需求和场景出发，再决定哪些表达适合保留。"
    )


def build_rule_diagnosis(payload: DiagnosisRequest) -> DiagnosisResponse:
    text = f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}"
    rule_scores = [
        _score_title(payload),
        _score_opening(payload),
        _score_structure(payload),
        _score_keyword_dimension("emotion_score", "情绪共鸣", text, PAIN_WORDS + ("焦虑", "安心", "终于", "减少遗漏"), 45, 9, "内容情绪触点不明显。", "加入真实困扰、踩坑经验或选择压力。"),
        _score_keyword_dimension("value_score", "信息价值", text, VALUE_WORDS, 42, 10, "内容可收藏的信息密度偏弱。", "补充步骤、清单、对比或总结。"),
        _score_keyword_dimension("interaction_score", "互动设计", text, ACTION_WORDS, 40, 10, "缺少评论区互动引导。", "结尾加入开放问题，引导用户在站内评论区交流。"),
        _score_tags(payload),
        _score_keyword_dimension("style_score", "平台风格匹配", text, STYLE_WORDS, 48, 8, "经验分享风格不够明显。", "适度加入真实、亲测、避坑、清单等经验型表达。"),
        _score_conversion(payload),
    ]

    overall = round(sum(item.score * WEIGHTS[item.key] for item in rule_scores))
    problems = [issue for item in rule_scores for issue in item.issues][:6]
    suggestions = [suggestion for item in rule_scores for suggestion in item.suggestions][:8]
    evidence_report = EvidenceBasedDiagnosisAgent().run(payload)
    recommended_tags = list(dict.fromkeys(payload.tags + [payload.category, payload.target_audience, payload.goal, "经验分享", "发布前检查", "内容优化"]))[:8]
    case_match = SimilarCaseAgent().match(payload)
    sample_insights = build_sample_insights(case_match.matched_samples, payload)
    rewritten_titles = [
        f"{payload.target_audience}做{payload.category}前，先看这 3 个检查点",
        f"我整理了一份{payload.category}发布前清单，适合{payload.target_audience}",
        f"{payload.category}别急着发布，先检查这几个关键信号",
    ]
    optimized_body = append_missing_detail_placeholders(_optimized_body(payload), payload)
    cover_text = [payload.cover_text or f"{payload.category}发布前检查", f"{payload.target_audience}先看", "3 个关键判断"]
    comment_guides = ["你现在最想优化标题、开头还是正文结构？可以在评论区说说。", "如果你也踩过类似坑，欢迎分享你的经验。"]
    risk_output = RiskReviewAgent().run(
        RiskReviewInput(
            payload=payload,
            rewritten_titles=rewritten_titles,
            optimized_body=optimized_body,
        )
    )
    score_items = [
        ScoreItem(key=item.key, name=item.name, score=item.score, weight=WEIGHTS[item.key], reason=item.reason, issues=item.issues, suggestions=item.suggestions)
        for item in rule_scores
    ]
    diagnosis_sources = build_diagnosis_sources(payload, case_match.matched_samples)
    score_deductions = build_score_deductions(payload, score_items)
    score_explanation = build_score_explanation(overall, score_deductions)
    evidence_diagnosis = build_evidence_diagnosis(
        payload,
        score_deductions,
        evidence_report.missing_user_inputs,
        risk_output.risks,
    )
    reader_perspectives = build_reader_perspectives(payload)
    revision_tasks = build_revision_tasks(evidence_diagnosis)

    if risk_output.risk_level == "high":
        rewritten_titles = []
        optimized_body = "\n".join(risk_output.safe_alternatives)

    return DiagnosisResponse(
        overall_score=overall,
        category=payload.category,
        summary="规则诊断已基于标题、开头、正文结构、可信细节、互动设计、标签和风险表达生成发布前优化建议。",
        scores=score_items,
        diagnosis_sources=diagnosis_sources,
        score_deductions=score_deductions,
        score_explanation=score_explanation,
        evidence_diagnosis=evidence_diagnosis,
        reader_perspectives=reader_perspectives,
        revision_tasks=revision_tasks,
        top_3_blockers=evidence_report.top_3_blockers,
        evidence_based_issues=evidence_report.evidence_based_issues,
        reader_reaction_simulation=evidence_report.reader_reaction_simulation,
        structure_analysis=evidence_report.structure_analysis,
        credibility_review=evidence_report.credibility_review,
        missing_user_inputs=evidence_report.missing_user_inputs,
        rewritten_versions=RewrittenVersions(
            titles=rewritten_titles,
            body=optimized_body,
            tags=recommended_tags,
            cover_text=cover_text,
            comment_guides=comment_guides,
        ),
        rewrite_explanations=build_rewrite_explanations(
            payload,
            rewritten_titles,
            optimized_body,
            recommended_tags,
            cover_text,
            comment_guides,
            evidence_diagnosis=evidence_diagnosis,
            revision_tasks=revision_tasks,
        ),
        risk_review=RiskReviewSummary(
            risk_level=risk_output.risk_level,
            overall_level=risk_output.risk_level,
            risk_items=risk_output.risk_items,
            safe_alternatives=risk_output.safe_alternatives,
            human_review_required=risk_output.human_review_required,
            risks=risk_output.risks,
            suggestions=risk_output.revision_suggestions,
        ),
        ai_disclosure_notice="当前为发布前优化诊断结果；系统不连接、不控制、不采集任何平台账号或平台数据，发布前请人工复核。",
        evidence_findings=evidence_report.evidence_findings,
        priority_actions=evidence_report.priority_actions,
        problems=problems or ["当前内容基础较完整，建议继续强化真实细节和结构层次。"],
        suggestions=list(dict.fromkeys((suggestions or ["可以进一步补充清单、步骤、对比和评论区开放问题。"]) + risk_output.revision_suggestions)),
        rewritten_titles=rewritten_titles,
        optimized_body=optimized_body,
        recommended_tags=recommended_tags,
        cover_text=cover_text,
        comment_guides=comment_guides,
        risks=risk_output.risks,
        matched_samples=case_match.matched_samples,
        case_match_message=case_match.message,
        sample_insights=sample_insights,
        mode="rule",
    )
