from fastapi.testclient import TestClient

from app.agents.similar_case_agent import SimilarCaseAgent
from app.main import app
from app.schemas.case import CaseMatchResponse, MatchedSample


client = TestClient(app)


def _payload() -> dict[str, object]:
    return {
        "title": "护肤新手怎么做",
        "content": "这个方法挺好用，大家可以试试。",
        "category": "护肤",
        "target_audience": "护肤新手",
        "goal": "收藏",
        "tags": ["护肤"],
        "cover_text": "护肤笔记",
        "comment_guide": "",
    }


def _matched_sample() -> MatchedSample:
    return MatchedSample(
        id=1,
        title="新手护肤避坑清单",
        category="护肤",
        tags=["护肤", "新手", "清单"],
        likes=120,
        collects=80,
        comments=10,
        similarity_score=0.8,
        similarity_reason="赛道相同；标签重合 2 个",
        what_to_learn=[
            "参考同赛道的选题角度和用户痛点表达。",
            "借鉴标题中的关键词组合方式，但不要复制原标题。",
            "参考正文的段落结构、步骤感或经验叙述方式。",
        ],
        suggested_adaptation="可以借鉴标题结构、标签组合和正文层次，再替换为自己的真实经历与具体细节。",
        caution="仅供结构参考，不建议照搬。",
    )


def test_sample_insights_returns_zero_without_samples(monkeypatch) -> None:
    monkeypatch.setattr(
        SimilarCaseAgent,
        "match",
        lambda self, payload, limit=3: CaseMatchResponse(matched_samples=[], message="暂无授权样本。"),
    )

    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    insights = response.json()["sample_insights"]
    assert insights["sample_count"] == 0
    assert "仅供结构参考" in insights["caution"]


def test_sample_insights_returns_structure_analysis_with_samples(monkeypatch) -> None:
    monkeypatch.setattr(
        SimilarCaseAgent,
        "match",
        lambda self, payload, limit=3: CaseMatchResponse(matched_samples=[_matched_sample()]),
    )

    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    insights = response.json()["sample_insights"]
    assert insights["sample_count"] == 1
    assert insights["reusable_structures"]
    assert insights["opening_patterns"]
    assert insights["title_patterns"]
    assert insights["trust_signals"]
    assert "仅供结构参考" in insights["caution"]


def test_sample_insights_caution_avoids_forbidden_promises(monkeypatch) -> None:
    monkeypatch.setattr(
        SimilarCaseAgent,
        "match",
        lambda self, payload, limit=3: CaseMatchResponse(matched_samples=[_matched_sample()]),
    )

    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    caution = response.json()["sample_insights"]["caution"]
    assert "仅供结构参考" in caution
    assert "保证" not in caution
    assert "必爆" not in caution
    assert "预测" not in caution
