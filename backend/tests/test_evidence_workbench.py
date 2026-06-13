import re

from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_client import OpenAIClient


client = TestClient(app)


def _payload(**overrides):
    payload = {
        "title": "护肤怎么做",
        "content": "这个护肤方法挺好用，大家可以试试。",
        "category": "护肤",
        "target_audience": "护肤新手",
        "goal": "收藏",
        "tags": ["护肤"],
        "cover_text": "护肤笔记",
        "comment_guide": "",
    }
    payload.update(overrides)
    return payload


def test_rule_diagnosis_returns_evidence_workbench_fields() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    body = response.json()

    assert body["diagnosis_sources"]
    assert body["score_deductions"]
    assert body["evidence_diagnosis"]
    assert body["reader_perspectives"]
    assert body["revision_tasks"]
    assert body["score_explanation"]
    assert len(body["revision_tasks"]) <= 3
    assert body["missing_user_inputs"]

    required_evidence_fields = {
        "evidence",
        "judgement",
        "why_it_matters",
        "confidence",
        "revision_principle",
        "example_fix",
    }
    for item in body["evidence_diagnosis"]:
        assert required_evidence_fields <= set(item)
        assert item["evidence"]
        assert item["judgement"]
        assert item["why_it_matters"]
        assert item["confidence"] in {"high", "medium", "low"}
        assert item["revision_principle"]
        assert item["example_fix"]


def test_rule_diagnosis_returns_score_explanation() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    body = response.json()
    explanation = body["score_explanation"]

    assert explanation["score"] == body["overall_score"]
    assert explanation["band"]
    assert explanation["interpretation"]
    assert len(explanation["main_loss_factors"]) <= 3
    assert explanation["next_score_goal"]
    assert "内容完整度与风险诊断分" in explanation["disclaimer"]
    assert "不是流量预测" in explanation["disclaimer"]
    assert "不承诺平台表现" in explanation["disclaimer"]
    assert "爆款预测" not in explanation["disclaimer"]
    assert "保证提升" not in explanation["disclaimer"]


def test_evidence_diagnosis_example_fix_does_not_invent_specific_results() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    body = response.json()
    example_fixes = "\n".join(item["example_fix"] for item in body["evidence_diagnosis"])

    invented_detail_patterns = [
        r"\d+\s*(天|周|月|年|小时|分钟)",
        r"(一|二|三|四|五|六|七|八|九|十|两)\s*(天|周|月|年|小时|分钟)",
        r"(提升|提高|增长|下降|减少)\s*\d+",
        r"\d+\s*%",
        r"(点赞|收藏|评论|涨粉|转化).*(翻倍|暴涨|增长|提升)",
        r"(一定|保证|绝对).*(有效|变好|提升)",
    ]
    assert not any(re.search(pattern, example_fixes) for pattern in invented_detail_patterns)
    assert "【" in example_fixes and "】" in example_fixes


def test_ai_diagnosis_keeps_rule_overall_score(monkeypatch) -> None:
    payload = _payload()
    rule_body = client.post("/api/diagnose/rule", json=payload).json()

    monkeypatch.setenv("USE_MOCK_AI", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-should-not-leak")

    def fake_generate_json(self, system_prompt, user_prompt):  # noqa: ANN001
        return {
            "overall_score": 100,
            "summary": "AI 只增强自然语言，不改变规则分数。",
            "problems": ["原文缺少真实场景，需要补充【请补充真实场景】。"],
            "suggestions": ["补充真实使用周期、观察到的变化和不适用情况。"],
            "rewritten_titles": ["护肤新手先看3个检查点", "护肤方法别急着照搬", "护肤前先确认适用边界"],
            "optimized_body": "这个方法需要补充【请补充真实使用周期】【请补充观察到的变化】【请补充不适用情况】。",
            "recommended_tags": ["护肤", "护肤新手", "经验分享"],
            "cover_text": ["护肤前先自查"],
            "risks": [{"level": "low", "message": "未发现高风险表达。"}],
        }

    monkeypatch.setattr(OpenAIClient, "generate_json", fake_generate_json)

    ai_response = client.post("/api/diagnose/ai", json=payload)

    assert ai_response.status_code == 200
    ai_body = ai_response.json()
    assert ai_body["mode"] == "ai"
    assert ai_body["overall_score"] == rule_body["overall_score"]
    assert ai_body["overall_score"] != 100
