import pytest
from pydantic import ValidationError

from app.schemas.diagnosis import DiagnosisResponse, EvidenceBasedIssue, RiskItem, ScoreItem


def test_evidence_based_issue_requires_supported_impact_and_severity() -> None:
    valid = EvidenceBasedIssue(
        field="标题",
        original_excerpt="护肤怎么做",
        issue="标题缺少明确人群和信息抓手。",
        why_it_matters="读者难以判断是否值得点击。",
        impact_area="click",
        severity="medium",
        rewrite_principle="补充目标人群、场景和具体数量。",
        example_fix="护肤新手先看这 3 个避坑点",
    )

    assert valid.impact_area == "click"
    assert valid.severity == "medium"

    with pytest.raises(ValidationError):
        EvidenceBasedIssue(
            field="标题",
            original_excerpt="护肤怎么做",
            issue="标题缺少明确人群和信息抓手。",
            why_it_matters="读者难以判断是否值得点击。",
            impact_area="traffic",
            severity="urgent",
            rewrite_principle="补充目标人群、场景和具体数量。",
            example_fix="护肤新手先看这 3 个避坑点",
        )


def test_diagnosis_response_exposes_evidence_report_defaults() -> None:
    response = DiagnosisResponse(
        overall_score=60,
        category="护肤",
        summary="本地规则诊断。",
        scores=[ScoreItem(name="标题吸引力", score=60, reason="测试")],
        problems=["标题信息抓手偏弱。"],
        suggestions=["补充具体人群和场景。"],
        rewritten_titles=["护肤新手先看这 3 个避坑点"],
        optimized_body="先说结论：请补充真实细节。",
        recommended_tags=["护肤", "新手"],
        cover_text=["护肤新手先看"],
        comment_guides=["你现在最困惑哪一步？"],
        risks=[RiskItem(level="low", message="未发现明显高风险表达。")],
    )
    body = response.model_dump()

    assert body["diagnosis_id"]
    assert body["category"] == "护肤"
    assert "top_3_blockers" in body
    assert "evidence_based_issues" in body
    assert "reader_reaction_simulation" in body
    assert "structure_analysis" in body
    assert "credibility_review" in body
    assert "missing_user_inputs" in body
    assert "rewritten_versions" in body
    assert "rewrite_explanations" in body
    assert "risk_review" in body
    assert body["ai_disclosure_notice"]
