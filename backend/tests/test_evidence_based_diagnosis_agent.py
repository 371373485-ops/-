from app.agents.evidence_based_diagnosis_agent import EvidenceBasedDiagnosisAgent
from app.schemas.diagnosis import DiagnosisRequest


def _payload(**overrides) -> DiagnosisRequest:
    data = {
        "category": "AI工具",
        "target_audience": "职场办公人群",
        "goal": "收藏",
        "title": "职场人用AI工具提效的3个真实场景",
        "content": (
            "先说结论：如果你每天都要写周报、整理会议纪要或总结资料，这类AI工具适合作为辅助。\n\n"
            "1. 我连续两周在写周报时使用，先列出本周事项，再整理成结构化表达。\n"
            "2. 开会后，我会对比人工记录和工具整理的行动清单，避免漏掉负责人。\n"
            "3. 但涉及客户数据和关键事实时，我会自己核对来源，不直接照搬。"
        ),
        "tags": ["AI工具", "职场办公", "效率工具", "经验分享"],
        "cover_text": "职场人AI提效清单",
        "comment_guide": "你最想用 AI 解决哪个办公场景？欢迎评论区聊聊。",
    }
    data.update(overrides)
    return DiagnosisRequest(**data)


def test_evidence_agent_returns_complete_report_for_normal_input() -> None:
    report = EvidenceBasedDiagnosisAgent().run(_payload())

    assert report.top_3_blockers
    assert len(report.top_3_blockers) <= 3
    assert report.evidence_based_issues
    assert report.reader_reaction_simulation.title_first_impression
    assert report.reader_reaction_simulation.after_first_three_lines
    assert report.reader_reaction_simulation.likely_drop_off_reason
    assert report.reader_reaction_simulation.strongest_interest_point
    assert report.reader_reaction_simulation.information_to_frontload
    assert report.structure_analysis.opening_hook
    assert report.structure_analysis.information_hierarchy
    assert report.structure_analysis.trust_building
    assert report.structure_analysis.detail_evidence
    assert report.structure_analysis.emotional_resonance
    assert report.structure_analysis.action_guidance
    assert isinstance(report.credibility_review.is_too_generic, bool)
    assert isinstance(report.credibility_review.sounds_like_ad, bool)


def test_evidence_agent_detects_generic_title() -> None:
    report = EvidenceBasedDiagnosisAgent().run(_payload(title="一个好用的工具"))

    title_issues = [issue for issue in report.evidence_based_issues if issue.field == "title"]
    assert title_issues
    assert title_issues[0].original_excerpt == "一个好用的工具"
    assert title_issues[0].impact_area == "click"
    assert title_issues[0].severity == "high"


def test_evidence_agent_returns_missing_user_inputs_when_trust_details_are_absent() -> None:
    report = EvidenceBasedDiagnosisAgent().run(
        _payload(
            title="一个好用的AI工具",
            content="这个工具很好用，可以提高效率，大家可以试试。",
            tags=["AI"],
            cover_text="好用工具",
            comment_guide="",
        )
    )

    missing_fields = {item.field for item in report.missing_user_inputs}
    assert "真实场景" in missing_fields
    assert "观察/使用周期" in missing_fields
    assert "记录到的变化" in missing_fields
    assert "失败或不适用情况" in missing_fields
    assert "适合/不适合人群" in missing_fields
    assert "不可公开信息边界" in missing_fields
    prompts = {item.suggested_prompt for item in report.missing_user_inputs}
    assert "这个经验来自什么真实场景？" in prompts
    assert "你观察/使用了多久？" in prompts
    assert "你记录了哪些变化？" in prompts
    assert "有没有失败或不适用情况？" in prompts
    assert "适合什么人，不适合什么人？" in prompts
    assert any("不能公开的信息" in prompt for prompt in prompts)
    assert any("不能替用户编造" in item.reason for item in report.missing_user_inputs)


def test_evidence_agent_issues_include_excerpt_and_why_it_matters() -> None:
    report = EvidenceBasedDiagnosisAgent().run(_payload(title="AI工具"))

    assert report.evidence_based_issues
    assert all(issue.original_excerpt for issue in report.evidence_based_issues)
    assert all(issue.why_it_matters for issue in report.evidence_based_issues)
