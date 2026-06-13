from collections.abc import Sequence

from app.schemas.diagnosis import (
    DiagnosisEvidenceSource,
    DiagnosisRequest,
    EvidenceDiagnosisItem,
    MissingUserInput,
    ReaderPerspective,
    RevisionTask,
    RiskItem,
    ScoreDeduction,
    ScoreExplanation,
    ScoreItem,
)


FIELD_LABELS = {
    "title_score": "标题",
    "opening_score": "正文开头",
    "structure_score": "正文结构",
    "emotion_score": "情绪共鸣",
    "value_score": "正文价值",
    "interaction_score": "评论引导",
    "tag_score": "标签",
    "style_score": "表达风格",
    "conversion_score": "行动判断",
}

IMPACT_BY_DIMENSION = {
    "标题": "click",
    "正文开头": "completion",
    "正文结构": "completion",
    "情绪共鸣": "trust",
    "正文价值": "collection",
    "评论引导": "interaction",
    "标签": "interaction",
    "表达风格": "trust",
    "行动判断": "trust",
    "风险表达": "compliance",
}

TASK_PRIORITY = {
    "compliance": 0,
    "click": 1,
    "completion": 2,
    "trust": 3,
    "collection": 4,
    "interaction": 5,
}


def build_diagnosis_sources(payload: DiagnosisRequest, matched_samples=None) -> list[DiagnosisEvidenceSource]:
    samples = _as_list(matched_samples)
    tags_provided = bool(payload.tags)
    has_cover_text = bool(payload.cover_text)
    has_comment_guide = bool(payload.comment_guide)

    return [
        DiagnosisEvidenceSource(
            field="title",
            provided=bool(payload.title),
            confidence="high" if payload.title else "low",
            note=_provided_note(payload.title, "标题已提供，可判断点击抓手、读者对象和风险表达。", "未提供标题，无法判断信息流点击入口。"),
        ),
        DiagnosisEvidenceSource(
            field="content",
            provided=bool(payload.content),
            confidence="high" if payload.content else "low",
            note=_provided_note(payload.content, "正文已提供，可判断开头、结构、可信细节和行动引导。", "未提供正文，无法做内容结构和可信细节诊断。"),
        ),
        DiagnosisEvidenceSource(
            field="category",
            provided=bool(payload.category),
            confidence="high" if payload.category else "low",
            note=_provided_note(payload.category, f"类目为“{payload.category}”，可用于判断赛道匹配。", "未提供类目，赛道判断可信度较低。"),
        ),
        DiagnosisEvidenceSource(
            field="target_audience",
            provided=bool(payload.target_audience),
            confidence="high" if payload.target_audience else "low",
            note=_provided_note(payload.target_audience, f"目标人群为“{payload.target_audience}”，可判断读者识别是否明确。", "未提供目标人群，读者视角模拟可信度较低。"),
        ),
        DiagnosisEvidenceSource(
            field="tags",
            provided=tags_provided,
            confidence="high" if len(payload.tags) >= 3 else "medium" if tags_provided else "low",
            note=(
                f"已提供 {len(payload.tags)} 个标签，可判断赛道、人群和内容形式覆盖度。"
                if len(payload.tags) >= 3
                else "标签已提供但数量偏少，只能做有限匹配判断。"
                if tags_provided
                else "未提供标签，无法判断标签覆盖度。"
            ),
        ),
        DiagnosisEvidenceSource(
            field="cover_text",
            provided=has_cover_text,
            confidence="medium" if has_cover_text else "low",
            note=(
                "已提供封面文案；当前只能判断文案信息强度，不能判断封面图片、排版和视觉表现。"
                if has_cover_text
                else "未提供封面文案，也未提供封面图片，无法判断封面承接能力。"
            ),
        ),
        DiagnosisEvidenceSource(
            field="comment_guide",
            provided=has_comment_guide,
            confidence="high" if has_comment_guide else "low",
            note=(
                "已提供评论引导，可判断是否合规、具体、适合站内互动。"
                if has_comment_guide
                else "未提供评论引导，只能从正文结尾推断互动设计。"
            ),
        ),
        DiagnosisEvidenceSource(
            field="matched_samples",
            provided=bool(samples),
            confidence="medium" if samples else "low",
            note=(
                f"已匹配到 {len(samples)} 条用户自有或授权样本，可做有限结构对标。"
                if samples
                else "未提供或未匹配到自有样本，不能做样本对标，只能基于当前输入诊断。"
            ),
        ),
    ]


def build_score_deductions(payload: DiagnosisRequest, scores: Sequence[ScoreItem]) -> list[ScoreDeduction]:
    deductions = []
    for score in scores:
        if not score.issues:
            continue
        dimension = FIELD_LABELS.get(score.key or "", score.name)
        points_lost = min(30, max(4, round((100 - score.score) * 0.35)))
        evidence = _evidence_for_dimension(payload, dimension)
        deductions.append(
            ScoreDeduction(
                dimension=dimension,
                points_lost=points_lost,
                reason="；".join(score.issues[:2]),
                evidence=evidence,
                improvement_path=_improvement_path_for_dimension(dimension, score.suggestions),
            )
        )
    return sorted(deductions, key=lambda item: item.points_lost, reverse=True)[:6]


def build_score_explanation(overall_score: int, score_deductions: Sequence[ScoreDeduction]) -> ScoreExplanation:
    if overall_score <= 59:
        band = "0-59"
        interpretation = "基础信息不足，优先补证据和合规风险。"
        next_score_goal = "先把标题对象、开头结论、真实场景、可信细节和风险表达补到可诊断状态，目标进入 60 分以上。"
    elif overall_score <= 69:
        band = "60-69"
        interpretation = "主题成立，但结构、细节或信任信号不足。"
        next_score_goal = "优先补齐正文结构、真实细节和站内行动引导，目标进入 70 分以上。"
    elif overall_score <= 79:
        band = "70-79"
        interpretation = "基础完整，适合发布前继续打磨。"
        next_score_goal = "围绕扣分最高的 1-2 个维度补证据、调开头和收紧表达边界，目标进入 80 分以上。"
    elif overall_score <= 89:
        band = "80-89"
        interpretation = "结构较完整，重点优化细节和表达边界。"
        next_score_goal = "继续检查真实细节、适用/不适用条件和合规措辞，目标接近 90 分。"
    else:
        band = "90-100"
        interpretation = "发布前完整度较高，仍需人工复核风险。"
        next_score_goal = "保持现有结构，发布前人工复核敏感表述、事实依据和不可公开信息。"

    return ScoreExplanation(
        score=overall_score,
        band=band,
        interpretation=interpretation,
        main_loss_factors=[deduction.reason for deduction in score_deductions[:3]],
        next_score_goal=next_score_goal,
        disclaimer="该分数是内容完整度与风险诊断分，不是流量预测，不承诺平台表现。",
    )


def build_evidence_diagnosis(
    payload: DiagnosisRequest,
    score_deductions: Sequence[ScoreDeduction],
    missing_user_inputs: Sequence[MissingUserInput],
    risks: Sequence[RiskItem],
) -> list[EvidenceDiagnosisItem]:
    items = [_diagnosis_from_deduction(deduction) for deduction in score_deductions]

    for missing in missing_user_inputs:
        items.append(
            EvidenceDiagnosisItem(
                field=missing.field,
                evidence=missing.reason,
                judgement="当前证据不足，系统不能替用户补全真实经历、数据、效果或身份背书。",
                why_it_matters="可信细节不足会削弱读者信任，也会让改写结果只能停留在模板层面。",
                impact_area="trust",
                confidence="high",
                severity="high" if "真实" in missing.field or "细节" in missing.field else "medium",
                revision_principle="先补充用户真实信息，再生成更具体的改写；没有证据时只使用占位模板。",
                example_fix=f"模板：{missing.suggested_prompt}",
                needs_user_input=True,
            )
        )

    for risk in risks:
        if risk.level == "low":
            continue
        items.append(
            EvidenceDiagnosisItem(
                field="风险表达",
                evidence=risk.message,
                judgement="内容存在需要优先处理的合规或信任风险。",
                why_it_matters="风险表达会削弱信任，严重时可能不适合继续生成营销化改写。",
                impact_area="compliance",
                confidence="high",
                severity="high" if risk.level == "high" else "medium",
                revision_principle="改成经验分享、过程复盘、适用边界或人工复核提醒，不承诺确定结果。",
                example_fix="基于我的真实场景，这些做法仅供参考，具体情况建议自行判断。",
                needs_user_input=False,
            )
        )

    if not any(item.field == "标题" for item in items):
        items.append(_positive_item("标题", _snippet(payload.title), "标题已有基础信息，但仍可检查是否更快点明目标读者和具体价值。", "click"))
    if not any(item.field in {"正文开头", "正文结构", "正文价值"} for item in items):
        items.append(_positive_item("正文结构", _snippet(payload.content), "正文已有基础结构，发布前仍建议检查开头、层次和收藏价值。", "completion"))
    if not any(item.field == "标签" for item in items):
        items.append(_positive_item("标签", "、".join(payload.tags) if payload.tags else "未提供标签", "标签没有明显高优先级问题，但可继续确认是否覆盖赛道、人群和内容形式。", "interaction"))
    if not any(item.field in {"评论引导", "风险表达"} for item in items):
        evidence = payload.comment_guide or _snippet(payload.content[-120:])
        items.append(_positive_item("评论引导", evidence, "互动设计没有明显高风险，但发布前仍应确认是否为站内开放问题。", "interaction"))

    return _dedupe_diagnosis_items(items)


def build_reader_perspectives(payload: DiagnosisRequest) -> list[ReaderPerspective]:
    opening = _first_paragraph(payload.content)
    ending = _snippet(payload.comment_guide or payload.content[-120:])
    risk_evidence = _risk_evidence(payload)
    return [
        ReaderPerspective(
            stage="feed",
            likely_reaction=f"读者会先用标题和封面判断这篇是否值得点开：{_snippet(payload.title)} / {_snippet(payload.cover_text or '未提供封面文案')}",
            trust_change="如果标题和封面能明确对象与价值，初始信任上升；如果泛泛而谈，信任停留较低。",
            action_intent="决定是否点击进入正文。",
            evidence=f"标题：{_snippet(payload.title)}；封面文案：{_snippet(payload.cover_text or '未提供')}",
        ),
        ReaderPerspective(
            stage="opening",
            likely_reaction=f"读者进入后会寻找适合谁、解决什么和为什么可信：{_snippet(opening)}",
            trust_change="开头有场景、结论或真实视角会提升信任；如果没有，读者容易离开。",
            action_intent="决定是否继续读完正文。",
            evidence=f"开头：{_snippet(opening)}",
        ),
        ReaderPerspective(
            stage="body",
            likely_reaction="读者会扫读正文是否有步骤、对比、条件和可收藏的信息。",
            trust_change="具体过程和限制条件越清楚，信任越高；只有结论会降低可信度。",
            action_intent="决定是否收藏、转发给自己或继续看后文。",
            evidence=f"正文片段：{_snippet(payload.content, 140)}",
        ),
        ReaderPerspective(
            stage="ending",
            likely_reaction=f"读者会看结尾是否给出明确、合规的站内互动入口：{ending}",
            trust_change="开放问题会让互动更自然；强迫互动或站外引流会降低信任。",
            action_intent="决定是否评论、收藏或补充自己的情况。",
            evidence=f"结尾/评论引导：{ending}",
        ),
        ReaderPerspective(
            stage="risk",
            likely_reaction="读者会对绝对承诺、收益承诺、功效承诺或站外引流保持警惕。",
            trust_change="风险表达越强，信任下降越明显；边界说明和人工复核提醒能降低疑虑。",
            action_intent="决定是否相信内容，或是否直接划走。",
            evidence=risk_evidence,
        ),
    ]


def build_revision_tasks(evidence_diagnosis: Sequence[EvidenceDiagnosisItem]) -> list[RevisionTask]:
    sorted_items = sorted(
        evidence_diagnosis,
        key=lambda item: (TASK_PRIORITY[item.impact_area], _severity_rank(item.severity)),
    )
    tasks = []
    for item in sorted_items[:3]:
        tasks.append(
            RevisionTask(
                rank=len(tasks) + 1,
                title=_task_title(item),
                target_field=item.field,
                reason=item.judgement,
                evidence=item.evidence,
                expected_effect=item.impact_area,
                suggested_action=item.revision_principle,
            )
        )
    return tasks


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if hasattr(value, "matched_samples"):
        return list(value.matched_samples)
    return list(value) if isinstance(value, tuple) else []


def _provided_note(value: str | None, provided_note: str, missing_note: str) -> str:
    return provided_note if value else missing_note


def _evidence_for_dimension(payload: DiagnosisRequest, dimension: str) -> str:
    if dimension == "标题":
        return _snippet(payload.title)
    if dimension == "正文开头":
        return _snippet(_first_paragraph(payload.content))
    if dimension in {"正文结构", "正文价值", "表达风格", "行动判断"}:
        return _snippet(payload.content, 140)
    if dimension == "标签":
        return "、".join(payload.tags) if payload.tags else "未提供标签"
    if dimension == "评论引导":
        return payload.comment_guide or _snippet(payload.content[-120:])
    return _snippet(payload.content or payload.title)


def _improvement_path_for_dimension(dimension: str, suggestions: Sequence[str]) -> str:
    if suggestions:
        return "；".join(suggestions[:2])
    paths = {
        "标题": "补充目标读者、具体场景和可验证的信息形式。",
        "正文开头": "前 2-3 句交代适合谁、解决什么、为什么继续看。",
        "正文结构": "拆成短段和编号，按判断点、步骤、适用边界组织。",
        "正文价值": "补充步骤、对比、真实观察和限制条件。",
        "标签": "补齐赛道、人群、内容形式和目标标签。",
        "评论引导": "改成站内开放问题，引导读者补充真实情况。",
    }
    return paths.get(dimension, "补充可验证证据和具体修改方向。")


def _diagnosis_from_deduction(deduction: ScoreDeduction) -> EvidenceDiagnosisItem:
    impact = IMPACT_BY_DIMENSION.get(deduction.dimension, "trust")
    severity = "high" if deduction.points_lost >= 20 else "medium" if deduction.points_lost >= 10 else "low"
    return EvidenceDiagnosisItem(
        field=deduction.dimension,
        evidence=deduction.evidence,
        judgement=deduction.reason,
        why_it_matters=_why_it_matters(impact),
        impact_area=impact,
        confidence="high" if deduction.evidence and deduction.evidence != "未提供标签" else "medium",
        severity=severity,
        revision_principle=deduction.improvement_path,
        example_fix=_example_fix_for_dimension(deduction.dimension),
        needs_user_input=False,
    )


def _why_it_matters(impact: str) -> str:
    return {
        "click": "点击前读者主要依赖标题和封面判断是否与自己有关。",
        "completion": "正文开头和结构决定读者是否愿意继续读完。",
        "collection": "可收藏价值来自清晰步骤、对比依据和可复用信息。",
        "trust": "可信细节会影响读者是否相信这是真实经验而非泛泛广告。",
        "interaction": "明确且合规的站内问题会提升评论意愿。",
        "compliance": "合规风险会直接影响内容能否安全发布和读者信任。",
    }[impact]


def _example_fix_for_dimension(dimension: str) -> str:
    examples = {
        "标题": "【目标人群】发布前先看：这 3 个检查点最影响点击",
        "正文开头": "如果你是【目标人群】，正在纠结【具体场景】，先看这 3 点。",
        "正文结构": "1. 先判断场景；2. 再列检查点；3. 最后补充适用和不适用条件。",
        "正文价值": "模板：我在【真实场景】中对比了【对象】，发现【真实观察】，但【限制条件】下需谨慎。",
        "标签": "#赛道 #目标人群 #经验分享 #发布前检查",
        "评论引导": "你现在最纠结哪一步？可以在评论区说说你的真实情况。",
    }
    return examples.get(dimension, "模板：基于【真实场景】补充【过程证据】和【适用边界】。")


def _positive_item(field: str, evidence: str, judgement: str, impact_area: str) -> EvidenceDiagnosisItem:
    return EvidenceDiagnosisItem(
        field=field,
        evidence=evidence,
        judgement=judgement,
        why_it_matters=_why_it_matters(impact_area),
        impact_area=impact_area,
        confidence="medium",
        severity="low",
        revision_principle="发布前复核是否有更具体的证据、边界和读者行动入口。",
        example_fix=_example_fix_for_dimension(field),
        needs_user_input=False,
    )


def _dedupe_diagnosis_items(items: Sequence[EvidenceDiagnosisItem]) -> list[EvidenceDiagnosisItem]:
    seen = set()
    unique = []
    for item in items:
        key = (item.field, item.evidence, item.judgement)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _task_title(item: EvidenceDiagnosisItem) -> str:
    if item.impact_area == "compliance":
        return "先处理合规风险"
    if item.impact_area == "click":
        return "重写点击入口"
    if item.impact_area == "completion":
        return "重排开头和正文结构"
    if item.impact_area == "trust":
        return "补足可信证据"
    if item.impact_area == "collection":
        return "强化收藏价值"
    return "优化站内互动入口"


def _severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}[severity]


def _first_paragraph(content: str) -> str:
    parts = [part.strip() for part in content.splitlines() if part.strip()]
    return parts[0] if parts else content[:80]


def _risk_evidence(payload: DiagnosisRequest) -> str:
    text = f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}\n{payload.comment_guide or ''}"
    risk_terms = ("保证", "绝对", "稳赚", "包治", "加微信", "私信", "扫码", "必涨粉", "全网最好")
    hits = [term for term in risk_terms if term in text]
    return "、".join(hits) if hits else "未发现明显绝对承诺、功效承诺、收益承诺或站外引流词。"


def _snippet(text: str | None, limit: int = 90) -> str:
    compact = " ".join((text or "").split())
    if not compact:
        return "未提供"
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
