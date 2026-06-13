import re

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(**overrides):
    payload = {
        "title": "一个好用的AI工具",
        "content": "这个工具挺好用，可以提高效率，大家可以试试。",
        "category": "AI工具",
        "target_audience": "职场办公人群",
        "goal": "收藏",
        "tags": ["AI"],
        "cover_text": "好用工具",
        "comment_guide": "",
    }
    payload.update(overrides)
    return payload


def test_rewrite_explanations_cover_every_rewritten_title_and_assets() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    body = response.json()
    explanations = body["rewrite_explanations"]
    targets = [item["target"] for item in explanations]

    assert len([target for target in targets if target.startswith("标题")]) == len(body["rewritten_titles"])
    assert "正文" in targets
    assert "标签" in targets
    assert any(target.startswith("封面文案") for target in targets)
    assert any(target.startswith("评论引导") for target in targets)
    assert all(item["reason"] for item in explanations)
    assert all(item["rewritten_excerpt"] for item in explanations)


def test_body_rewrite_explanation_describes_frontload_weakening_trust_and_effect() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    body_reason = next(item["reason"] for item in response.json()["rewrite_explanations"] if item["target"] == "正文")

    assert "前置信息" in body_reason
    assert "删除或弱化" in body_reason
    assert "可信信号提示" in body_reason
    assert "提升完读和信任" in body_reason
    assert "合规风险" in body_reason


def test_missing_real_details_use_placeholders_in_rewrite() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    body = response.json()
    optimized_body = body["optimized_body"]
    explanation_text = " ".join(item["reason"] for item in body["rewrite_explanations"])

    assert "【请补充真实场景】" in optimized_body
    assert "【请补充真实使用周期】" in optimized_body
    assert "【请补充观察到的变化】" in optimized_body
    assert "【请补充不适用情况】" in optimized_body
    assert "【请补充真实使用周期】" in explanation_text
    assert "【请补充观察到的变化】" in explanation_text


def test_rewrite_explanations_link_to_diagnosis_evidence() -> None:
    payload = _payload()
    response = client.post("/api/diagnose/rule", json=payload)

    assert response.status_code == 200
    body = response.json()
    explanations = body["rewrite_explanations"]
    linked = [item for item in explanations if item.get("source_evidence")]
    rule_evidence = {item["evidence"] for item in body["evidence_diagnosis"]}
    user_inputs = "\n".join(
        [
            payload["title"],
            payload["content"],
            payload["category"],
            payload["target_audience"],
            "、".join(payload["tags"]),
            payload["cover_text"],
            payload["comment_guide"],
        ]
    )

    assert linked
    for item in linked:
        assert item["source_evidence"] in rule_evidence or item["source_evidence"] in user_inputs
        assert item.get("source_issue_field")


def test_rewrite_explanations_do_not_invent_user_data_or_effects() -> None:
    response = client.post("/api/diagnose/rule", json=_payload())

    assert response.status_code == 200
    explanation_text = "\n".join(
        " ".join(
            str(item.get(field) or "")
            for field in ("reason", "source_evidence", "rewritten_excerpt")
        )
        for item in response.json()["rewrite_explanations"]
    )

    invented_patterns = [
        r"\d+\s*(天|周|月|年|小时|分钟)",
        r"(提升|提高|增长|下降|减少)\s*\d+",
        r"\d+\s*%",
        r"\d+\s*(个|次|万|k|K)?\s*(点赞|收藏|评论|涨粉|转化)",
        r"(保证|一定有效|绝对有效|一定变好|绝对变好)",
    ]
    matches = [re.search(pattern, explanation_text).group(0) for pattern in invented_patterns if re.search(pattern, explanation_text)]
    assert not matches
