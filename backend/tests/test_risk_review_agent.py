from app.agents.risk_review_agent import RiskReviewAgent
from app.schemas.diagnosis import DiagnosisRequest
from app.schemas.workflow import RiskReviewInput


def _payload(**overrides) -> DiagnosisRequest:
    data = {
        "category": "护肤",
        "target_audience": "护肤新手",
        "goal": "收藏",
        "title": "护肤新手避坑清单",
        "content": "我整理了自己的真实护肤步骤，仅供参考。",
        "tags": ["护肤", "新手"],
        "cover_text": "护肤先看",
        "comment_guide": "你最困惑哪一步？欢迎评论区聊聊。",
    }
    data.update(overrides)
    return DiagnosisRequest(**data)


def test_risk_review_agent_flags_triggered_terms_with_evidence() -> None:
    output = RiskReviewAgent().run(
        RiskReviewInput(
            payload=_payload(
                title="这个方法保证立刻见效",
                content="任何人用了都能变好，私信领资料。",
                comment_guide="加微信进群。",
            )
        )
    )

    triggered = {item.triggered_text for item in output.risk_items}
    risk_types = {item.risk_type for item in output.risk_items}
    assert "保证" in triggered
    assert "立刻见效" in triggered
    assert "私信领" in triggered
    assert "加微信" in triggered
    assert "绝对化表达" in risk_types
    assert "夸大功效" in risk_types
    assert "站外引流" in risk_types
    assert all(item.field for item in output.risk_items)
    assert all(item.reason for item in output.risk_items)
    assert all(item.suggested_rewrite for item in output.risk_items)


def test_high_risk_requires_human_review() -> None:
    output = RiskReviewAgent().run(
        RiskReviewInput(
            payload=_payload(
                category="理财",
                title="这个理财方法稳赚保本",
                content="跟着做收益翻倍，无风险。",
            )
        )
    )

    assert output.risk_level == "high"
    assert output.human_review_required is True
    assert any(item.risk_type == "金融理财风险" for item in output.risk_items)


def test_risk_review_generates_safe_alternatives() -> None:
    output = RiskReviewAgent().run(
        RiskReviewInput(
            payload=_payload(
                title="医生推荐的祛痘根治方法",
                content="不用去医院，照着做就能治好。",
            )
        )
    )

    alternatives = " ".join(output.safe_alternatives)
    assert "专业人士" in alternatives or "就医" in alternatives
    assert "不继续生成营销化标题" in alternatives
    assert "不得替用户编造资质" in " ".join(output.revision_suggestions)


def test_ai_disclosure_notice_is_present_without_escalating_risk_level() -> None:
    output = RiskReviewAgent().run(RiskReviewInput(payload=_payload()))

    assert output.risk_level == "low"
    assert output.human_review_required is False
    assert any(item.risk_type == "AI 生成内容披露提醒" for item in output.risk_items)
