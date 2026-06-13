from app.agents.evidence_based_diagnosis_agent import EvidenceBasedDiagnosisAgent
from app.agents.risk_review_agent import RiskReviewAgent
from app.agents.similar_case_agent import SimilarCaseAgent
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse, EvidenceFinding, PriorityAction, RewrittenVersions, RiskItem, ScoreItem
from app.schemas.workflow import RiskReviewInput
from app.services.rewrite_explanation_service import append_missing_detail_placeholders, build_rewrite_explanations
from app.services.sample_insight_service import build_sample_insights


HIGH_RISK_TERMS = ("绝对", "保证", "稳赚", "包治", "加微信", "私信领", "全网最好", "永久有效")


def _score_title(title: str) -> int:
    score = 58
    if 8 <= len(title) <= 30:
        score += 16
    if any(mark in title for mark in ("?", "？", "!", "！", "|")):
        score += 8
    if any(word in title for word in ("清单", "避坑", "新手", "真实", "教程", "实测")):
        score += 10
    return min(score, 100)


def _score_content(content: str) -> int:
    score = 56
    if len(content) >= 120:
        score += 12
    if any(marker in content for marker in ("1.", "①", "第一", "- ", "首先")):
        score += 10
    if any(word in content for word in ("经历", "实测", "对比", "总结", "踩坑")):
        score += 10
    return min(score, 100)


def _score_goal_fit(goal: str, content: str) -> int:
    goal_keywords = {
        "涨粉": ("关注", "持续", "系列"),
        "收藏": ("清单", "步骤", "保存", "整理"),
        "引流": ("评论", "留言", "交流"),
        "转化": ("适合", "选择", "对比"),
        "种草": ("体验", "喜欢", "推荐", "实测"),
    }
    score = 60
    score += sum(8 for keyword in goal_keywords.get(goal, ()) if keyword in content)
    return min(score, 100)


def _risk_items(text: str) -> list[RiskItem]:
    found = [term for term in HIGH_RISK_TERMS if term in text]
    if not found:
        return [RiskItem(level="low", message="未发现明显高风险表达，发布前仍建议人工复核。")]
    return [RiskItem(level="medium", message=f"检测到可能需要降风险处理的表达：{', '.join(found)}。建议改为经验分享、适用场景或个人感受。")]


def _optimized_body(payload: DiagnosisRequest) -> str:
    topic = payload.category
    audience = payload.target_audience
    return (
        f"我把这次{topic}相关经验整理给{audience}参考。\n\n"
        f"先说结论：这类内容最容易踩坑的地方，不是知道得不够多，而是没有把场景、需求和执行步骤拆清楚。\n\n"
        "可以按这 3 步来判断：\n"
        "1. 先确认自己的真实需求，不要只被单个案例带着走。\n"
        "2. 对比关键差异，优先选择更适合自己当前阶段的方案。\n"
        "3. 执行后记录反馈，再根据结果微调。\n\n"
        "这篇更适合作为入门参考，不代表所有人都适用。你也可以结合自己的情况做取舍。"
    )


def _mock_evidence(payload: DiagnosisRequest) -> list[EvidenceFinding]:
    opening = " ".join(payload.content.split())[:80]
    findings = [
        EvidenceFinding(
            priority="P0",
            dimension="点击",
            source="标题",
            evidence=payload.title,
            issue="标题需要更快说明读者是谁、在什么场景下能获得什么。",
            impact="点击前的信息判断不够明确，会削弱目标用户打开笔记的理由。",
            action=f"改成“{payload.target_audience} + {payload.category}场景 + 3 个具体判断/清单”。",
        ),
        EvidenceFinding(
            priority="P1",
            dimension="完读/信任",
            source="正文开头",
            evidence=opening,
            issue="正文需要把结论、问题和适用边界放得更靠前。",
            impact="读者需要读到后面才知道价值点，完读和信任建立都会变慢。",
            action="第一段先给结论，再用编号补充步骤、对比或适用提醒。",
        ),
    ]
    risk_terms = [term for term in HIGH_RISK_TERMS if term in f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}"]
    if risk_terms:
        findings.insert(
            0,
            EvidenceFinding(
                priority="P0",
                dimension="合规/信任",
                source="标题/正文/封面",
                evidence="、".join(risk_terms),
                issue="存在绝对化、夸大承诺或站外引流风险表达。",
                impact="这类表达会降低可信度，并可能带来合规风险。",
                action="改为个人经验、适用场景和人工复核提醒，不承诺确定效果。",
            ),
        )
    return findings


def _priority_actions(findings: list[EvidenceFinding]) -> list[PriorityAction]:
    return [
        PriorityAction(
            priority=index + 1,
            action=finding.action,
            reason=f"{finding.source}证据显示：{finding.issue}",
            expected_effect=f"优先改善{finding.dimension}。{finding.impact}",
        )
        for index, finding in enumerate(findings[:5])
    ]


def build_mock_diagnosis(payload: DiagnosisRequest) -> DiagnosisResponse:
    title_score = _score_title(payload.title)
    content_score = _score_content(payload.content)
    tag_score = min(100, 55 + len(payload.tags) * 7)
    goal_score = _score_goal_fit(payload.goal, payload.content)
    risk_penalty = 8 if any(term in f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}" for term in HIGH_RISK_TERMS) else 0
    overall = max(0, round((title_score * 0.3 + content_score * 0.35 + tag_score * 0.15 + goal_score * 0.2) - risk_penalty))

    topic = payload.category
    audience = payload.target_audience
    recommended_tags = list(dict.fromkeys(payload.tags + [topic, audience, payload.goal, "经验分享", "新手友好", "真实测评"]))[:8]
    case_match = SimilarCaseAgent().match(payload)
    sample_insights = build_sample_insights(case_match.matched_samples, payload)
    evidence_report = EvidenceBasedDiagnosisAgent().run(payload)
    rewritten_titles = [f"{audience}做{topic}前，先看完这份避坑清单", f"真实体验后，我整理了这 3 个{topic}关键点", f"{topic}怎么更适合{audience}？一篇讲清思路"]
    optimized_body = append_missing_detail_placeholders(_optimized_body(payload), payload)
    cover_text = [payload.cover_text or f"{topic}避坑清单", f"{audience}先看这篇", "真实经验整理"]
    comment_guides = ["你现在最想优化哪一部分？可以留言说说你的情况。", "如果你也遇到类似问题，欢迎分享你的经验。"]
    risk_output = RiskReviewAgent().run(
        RiskReviewInput(
            payload=payload,
            rewritten_titles=rewritten_titles,
            optimized_body=optimized_body,
        )
    )
    risks = risk_output.risks

    return DiagnosisResponse(
        overall_score=overall,
        category=payload.category,
        summary="这是 mock 模式生成的演示诊断结果，用于无 API Key 场景下完成前后端联调和产品演示。",
        scores=[
            ScoreItem(name="标题吸引力", score=title_score, reason="根据标题长度、符号、场景词和信息密度进行规则评分。"),
            ScoreItem(name="正文结构", score=content_score, reason="根据篇幅、分段、步骤感和经验型表达进行规则评分。"),
            ScoreItem(name="目标匹配", score=goal_score, reason=f"根据发布目标“{payload.goal}”与正文表达的匹配度进行估算。"),
            ScoreItem(name="标签完整度", score=tag_score, reason="根据原始标签数量和主题覆盖度进行保守评分。"),
        ],
        top_3_blockers=evidence_report.top_3_blockers,
        evidence_based_issues=evidence_report.evidence_based_issues,
        reader_reaction_simulation=evidence_report.reader_reaction_simulation,
        structure_analysis=evidence_report.structure_analysis,
        credibility_review=evidence_report.credibility_review,
        missing_user_inputs=evidence_report.missing_user_inputs,
        rewritten_versions=RewrittenVersions(
            titles=[] if risk_output.risk_level == "high" else rewritten_titles,
            body="\n".join(risk_output.safe_alternatives) if risk_output.risk_level == "high" else optimized_body,
            tags=recommended_tags,
            cover_text=cover_text,
            comment_guides=comment_guides,
        ),
        rewrite_explanations=build_rewrite_explanations(payload, rewritten_titles, optimized_body, recommended_tags, cover_text, comment_guides),
        risk_review={
            "risk_level": risk_output.risk_level,
            "overall_level": risk_output.risk_level,
            "risk_items": risk_output.risk_items,
            "safe_alternatives": risk_output.safe_alternatives,
            "human_review_required": risk_output.human_review_required,
            "risks": risks,
            "suggestions": risk_output.revision_suggestions,
        },
        ai_disclosure_notice="当前为 mock 演示诊断，未调用真实 OpenAI API，也未调用小红书平台接口；结果仅供本地演示和人工复核。",
        evidence_findings=evidence_report.evidence_findings,
        priority_actions=evidence_report.priority_actions,
        problems=["开头可以更快点明读者是谁、能获得什么。", "正文需要更明确的结构层次，建议加入步骤、对比或场景化细节。", "发布目标还可以更明显地体现在结尾行动引导中。"],
        suggestions=list(dict.fromkeys(["标题优先使用“人群 + 场景 + 明确收益”的结构，但避免绝对化承诺。", "正文建议采用“结论先行 - 关键问题 - 具体步骤 - 适用提醒”的结构。", "标签覆盖赛道、人群、目标和内容形式，避免只堆泛标签。", "风险表达要从承诺式话术改成经验式、建议式表达。"] + risk_output.revision_suggestions)),
        rewritten_titles=[] if risk_output.risk_level == "high" else rewritten_titles,
        optimized_body="\n".join(risk_output.safe_alternatives) if risk_output.risk_level == "high" else optimized_body,
        recommended_tags=recommended_tags,
        cover_text=cover_text,
        comment_guides=comment_guides,
        risks=risks,
        matched_samples=case_match.matched_samples,
        case_match_message=case_match.message,
        sample_insights=sample_insights,
    )
