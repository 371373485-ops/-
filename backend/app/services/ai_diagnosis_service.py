import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.prompts.body_rewrite_prompt import BODY_REWRITE_PROMPT
from app.prompts.diagnosis_prompt import DIAGNOSIS_PROMPT
from app.prompts.risk_review_prompt import RISK_REVIEW_PROMPT
from app.prompts.tag_cover_prompt import TAG_COVER_PROMPT
from app.prompts.title_rewrite_prompt import TITLE_REWRITE_PROMPT
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse, RewrittenVersions, RiskItem
from app.services.ai_client import AIClientError, OpenAIClient, should_use_mock_ai
from app.services.ai_providers.base import AIInvalidJSONError
from app.services.rewrite_explanation_service import build_rewrite_explanations
from app.services.scoring_service import build_rule_diagnosis


class AIContent(BaseModel):
    summary: str = Field(..., min_length=1)
    problems: list[str] = Field(..., min_length=1, max_length=8)
    suggestions: list[str] = Field(..., min_length=1, max_length=10)
    rewritten_titles: list[str] = Field(..., min_length=3, max_length=3)
    optimized_body: str = Field(..., min_length=1)
    recommended_tags: list[str] = Field(..., min_length=3, max_length=10)
    cover_text: list[str] = Field(..., min_length=1, max_length=5)
    risks: list[RiskItem] = Field(..., min_length=1)


def _system_prompt() -> str:
    return "\n\n".join(
        [
            DIAGNOSIS_PROMPT,
            TITLE_REWRITE_PROMPT,
            BODY_REWRITE_PROMPT,
            TAG_COVER_PROMPT,
            RISK_REVIEW_PROMPT,
            (
                "真实 AI 只负责自然语言增强和改写，不重新评分，不覆盖本地规则生成的分数、"
                "证据来源、扣分项、证据型诊断、读者视角和修订任务。"
            ),
            (
                "禁止使用空话：优化表达、增强吸引力、突出卖点、提升内容质量。"
                "除非同一句或同一条中同时给出原文证据、明确问题、影响指标和具体改法。"
            ),
            "不得编造真实经历、数据、平台表现、使用效果、身份背书、案例或用户反馈。",
            "缺少真实细节时，必须使用【请补充...】占位提示，或明确提示用户补充，不能自行补全。",
            "你必须只输出一个合法 JSON object。不要输出 Markdown，不要使用 ```json 代码块，不要解释 JSON 外的内容。",
        ]
    )


def _user_prompt(payload: DiagnosisRequest, rule_result: DiagnosisResponse) -> str:
    request_data = payload.model_dump()
    rule_data = {
        "overall_score": rule_result.overall_score,
        "scores": [item.model_dump() for item in rule_result.scores],
        "rule_problems": rule_result.problems,
        "rule_suggestions": rule_result.suggestions,
    }
    return f"""
请基于以下用户手动输入内容和规则评分结果，生成更自然的诊断与改写。

你的职责边界：
- 只做自然语言增强和改写，不重新计算 overall_score。
- 不覆盖规则生成的 diagnosis_sources、score_deductions、evidence_diagnosis、reader_perspectives、revision_tasks。
- 不输出 overall_score、scores、diagnosis_sources、score_deductions、evidence_diagnosis、reader_perspectives、revision_tasks。
- 不编造真实经历、数据、平台表现、使用效果、身份背书、案例或用户反馈。
- 缺少细节时必须使用占位提示，例如【请补充真实使用周期】【请补充观察到的变化】【请补充不适用情况】，或提示用户补充。
- 禁止空话：优化表达、增强吸引力、突出卖点、提升内容质量；除非同时给出原文证据、明确问题、影响指标和具体改法。

用户输入：
{json.dumps(request_data, ensure_ascii=False)}

规则评分结果：
{json.dumps(rule_data, ensure_ascii=False)}

输出必须是紧凑 JSON，避免输出过长。不要复述规则评分里的长证据；证据型诊断由本地规则结果保留。

输出 JSON 必须包含以下字段：
- summary: string
- problems: string[]，最多 4 条
- suggestions: string[]，最多 5 条
- rewritten_titles: string[]，必须 3 个
- optimized_body: string，控制在 800 个中文字符以内
- recommended_tags: string[]，3 到 8 个
- cover_text: string[]，1 到 3 个
- risks: array，元素包含 level 和 message，最多 3 条

再次强调：只返回 JSON object 本身，第一字符必须是 {{，最后字符必须是 }}。
"""


def _merge_ai_content(payload: DiagnosisRequest, rule_result: DiagnosisResponse, ai_content: AIContent) -> DiagnosisResponse:
    rewritten_versions = RewrittenVersions(
        titles=ai_content.rewritten_titles,
        body=ai_content.optimized_body,
        tags=ai_content.recommended_tags,
        cover_text=ai_content.cover_text,
        comment_guides=rule_result.comment_guides,
    )
    return DiagnosisResponse(
        overall_score=rule_result.overall_score,
        category=rule_result.category,
        summary=ai_content.summary,
        scores=rule_result.scores,
        diagnosis_sources=rule_result.diagnosis_sources,
        score_deductions=rule_result.score_deductions,
        score_explanation=rule_result.score_explanation,
        evidence_diagnosis=rule_result.evidence_diagnosis,
        reader_perspectives=rule_result.reader_perspectives,
        revision_tasks=rule_result.revision_tasks,
        top_3_blockers=rule_result.top_3_blockers,
        evidence_based_issues=rule_result.evidence_based_issues,
        reader_reaction_simulation=rule_result.reader_reaction_simulation,
        structure_analysis=rule_result.structure_analysis,
        credibility_review=rule_result.credibility_review,
        missing_user_inputs=rule_result.missing_user_inputs,
        rewritten_versions=rewritten_versions,
        rewrite_explanations=build_rewrite_explanations(
            payload=payload,
            rewritten_titles=ai_content.rewritten_titles,
            optimized_body=ai_content.optimized_body,
            recommended_tags=ai_content.recommended_tags,
            cover_text=ai_content.cover_text,
            comment_guides=rule_result.comment_guides,
            evidence_diagnosis=rule_result.evidence_diagnosis,
            revision_tasks=rule_result.revision_tasks,
        ),
        risk_review=rule_result.risk_review,
        ai_disclosure_notice="当前结果合并了本地规则诊断与真实 AI 输出；未调用小红书平台接口，发布前请人工复核。",
        evidence_findings=rule_result.evidence_findings,
        priority_actions=rule_result.priority_actions,
        problems=ai_content.problems,
        suggestions=ai_content.suggestions,
        rewritten_titles=ai_content.rewritten_titles,
        optimized_body=ai_content.optimized_body,
        recommended_tags=ai_content.recommended_tags,
        cover_text=ai_content.cover_text,
        comment_guides=rule_result.comment_guides,
        risks=ai_content.risks,
        matched_samples=rule_result.matched_samples,
        case_match_message=rule_result.case_match_message,
        sample_insights=rule_result.sample_insights,
        mode="ai",
    )


def _repair_prompt(raw_content: str) -> str:
    return f"""
下面是一段 AI Provider 返回内容。它不是后端可解析的合法 JSON。

请把它改写为一个合法 JSON object，只保留 JSON，不要 Markdown，不要解释。

必须包含字段：
- summary: string
- problems: string[]
- suggestions: string[]
- rewritten_titles: string[]，必须 3 个
- optimized_body: string
- recommended_tags: string[]，至少 3 个
- cover_text: string[]，至少 1 个
- risks: array，元素包含 level 和 message

如果原文缺少某些字段，请用保守、合规、非编造的内容补齐结构，但不得编造真实经历、数据、效果或案例。
不得补充或修复出 overall_score、scores、diagnosis_sources、score_deductions、evidence_diagnosis、reader_perspectives、revision_tasks、evidence_findings、priority_actions。

待修复内容：
{raw_content[:6000]}
"""


def _generate_ai_content_with_repair(client: OpenAIClient, system_prompt: str, user_prompt: str) -> AIContent:
    try:
        raw_content: dict[str, Any] = client.generate_json(system_prompt, user_prompt)
        return AIContent.model_validate(raw_content)
    except AIInvalidJSONError as exc:
        repaired_content = client.generate_json(
            "你是 JSON 修复器。你只输出合法 JSON object，不输出 Markdown 或额外解释。",
            _repair_prompt(exc.raw_content),
        )
        return AIContent.model_validate(repaired_content)


def build_ai_diagnosis(payload: DiagnosisRequest) -> DiagnosisResponse:
    rule_result = build_rule_diagnosis(payload)
    client = OpenAIClient()

    if should_use_mock_ai() or not client.is_configured:
        rule_result.mode = "ai_mock"
        rule_result.summary = "AI mock 模式：未调用真实 OpenAI API，当前结果由本地规则评分生成，可用于本地演示。"
        return rule_result

    try:
        ai_content = _generate_ai_content_with_repair(client, _system_prompt(), _user_prompt(payload, rule_result))
    except AIClientError as exc:
        rule_result.mode = "ai_fallback"
        rule_result.summary = f"真实 AI 调用失败，已自动降级为本地规则诊断。原因：{exc}"
        return rule_result
    except ValidationError:
        rule_result.mode = "ai_fallback"
        rule_result.summary = "真实 AI 返回结构不符合预期，已自动降级为本地规则诊断。"
        return rule_result

    return _merge_ai_content(payload, rule_result, ai_content)
