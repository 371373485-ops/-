import re

from fastapi.testclient import TestClient

from app.main import app
from app.services.scoring_service import build_rule_diagnosis
from app.schemas.diagnosis import DiagnosisRequest


client = TestClient(app)


def _payload() -> dict[str, object]:
    return {
        "category": "护肤",
        "target_audience": "护肤新手",
        "goal": "互动",
        "title": "护肤怎么做",
        "content": "好用，大家可以试试。",
        "tags": ["护肤"],
        "cover_text": "护肤笔记",
        "comment_guide": None,
    }


def test_refine_diagnosis_returns_200_and_uses_user_supplied_evidence() -> None:
    original_payload = _payload()

    response = client.post(
        "/api/diagnose/refine",
        json={
            "original_payload": original_payload,
            "missing_answers": [
                {"field": "真实场景", "answer": "晚上护肤后记录皮肤状态"},
                {"field": "观察/使用周期", "answer": "连续两周"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    raw = response.text
    assert body["mode"] == "rule"
    assert "用户补充信息" in raw
    assert "晚上护肤后记录皮肤状态" in raw
    assert "连续两周" in raw


def test_refine_diagnosis_missing_inputs_do_not_increase() -> None:
    original_payload = _payload()
    original_result = build_rule_diagnosis(DiagnosisRequest(**original_payload))

    response = client.post(
        "/api/diagnose/refine",
        json={
            "original_payload": original_payload,
            "missing_answers": [
                {"field": "真实场景", "answer": "晚上护肤后记录皮肤状态"},
                {"field": "观察/使用周期", "answer": "连续两周"},
                {"field": "记录到的变化", "answer": "只记录泛红和干燥感变化，不写确定功效"},
                {"field": "失败或不适用情况", "answer": "敏感期不适合直接照搬"},
            ],
        },
    )

    assert response.status_code == 200
    refined = response.json()
    assert len(refined["missing_user_inputs"]) <= len(original_result.missing_user_inputs)


def test_refine_diagnosis_does_not_fabricate_platform_performance_data() -> None:
    response = client.post(
        "/api/diagnose/refine",
        json={
            "original_payload": _payload(),
            "missing_answers": [
                {"field": "真实体验依据", "answer": "只基于自己的护肤记录，不包含任何平台数据"},
            ],
        },
    )

    assert response.status_code == 200
    raw = response.text
    assert "涨粉" not in raw
    assert "点赞" not in raw
    assert not re.search(r"\d+\s*(个|次|万|k|K)?\s*(点赞|收藏|涨粉)", raw)
