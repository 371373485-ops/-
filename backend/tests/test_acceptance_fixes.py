from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_samples_csv_exists_and_imports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAMPLE_DB_PATH", str(tmp_path / "samples.sqlite3"))
    demo_path = Path(__file__).resolve().parents[2] / "demo_samples.csv"

    assert demo_path.exists()

    response = client.post(
        "/api/samples/import",
        files={"file": ("demo_samples.csv", demo_path.read_bytes(), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["imported_count"] >= 1
    assert all(sample["source_type"] == "demo_generated" for sample in body["samples"])
    assert all("虚构演示样本" in sample["source_note"] for sample in body["samples"])


def test_acceptance_risk_review_flags_growth_promises(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAMPLE_DB_PATH", str(tmp_path / "samples.sqlite3"))
    payload = {
        "category": "涨粉",
        "target_audience": "内容创作者",
        "goal": "涨粉",
        "title": "这个方法保证让你7天涨粉10万",
        "content": "只要按照我这个方法做，任何人都能快速爆火，保证涨粉，保证变现。",
        "tags": ["涨粉", "变现", "爆款"],
        "cover_text": "",
    }

    response = client.post("/api/diagnose/workflow", json=payload)

    assert response.status_code == 200
    body = response.json()
    risk_text = " ".join(risk["message"] for risk in body["risks"])
    suggestion_text = " ".join(body["suggestions"])
    assert "保证" in risk_text
    assert "任何人" in risk_text
    assert "7天涨粉10万" in risk_text
    assert "经验分享" in suggestion_text or "案例复盘" in suggestion_text
    assert "只要按照我这个方法做" not in body["optimized_body"]
    assert "保证涨粉" not in body["optimized_body"]


def test_acceptance_quality_content_gets_reasonable_explainable_result(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAMPLE_DB_PATH", str(tmp_path / "samples.sqlite3"))
    payload = {
        "category": "AI工具",
        "target_audience": "职场办公人群",
        "goal": "收藏",
        "title": "职场人用AI工具提效的3个场景",
        "content": (
            "先说结论：如果你每天都要写周报、整理会议纪要或总结资料，这类AI工具很适合先收藏。\n\n"
            "1. 写周报时，先列出本周事项，再让工具帮你整理成结构化表达。\n"
            "2. 开会后，把要点整理成行动清单，减少遗漏。\n"
            "3. 查资料时，先让工具归纳重点，再自己核对来源和细节。\n\n"
            "最后提醒：AI只能辅助整理，关键事实还是要自己确认。你最想用它解决哪个办公场景？欢迎评论区聊聊。"
        ),
        "tags": ["AI工具", "职场办公", "效率工具", "收藏清单"],
        "cover_text": "职场人AI提效清单",
    }

    response = client.post("/api/diagnose/workflow", json=payload)

    assert response.status_code == 200
    body = response.json()
    problem_text = " ".join(body["problems"])
    assert body["overall_score"] >= 75
    assert "标题没有明确具体对象" not in problem_text
    assert "开头没有快速点名目标人群" not in problem_text
    assert "正文信息量偏少" not in problem_text
    assert any(score["key"] == "title_score" and score["score"] >= 80 for score in body["scores"])
    assert any(score["key"] == "structure_score" and score["score"] >= 85 for score in body["scores"])
    assert any("评论" in guide for guide in body["comment_guides"])


def test_acceptance_weak_content_gets_clear_diagnosis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAMPLE_DB_PATH", str(tmp_path / "samples.sqlite3"))
    payload = {
        "category": "AI工具",
        "target_audience": "职场办公人群",
        "goal": "收藏",
        "title": "一个好用的AI工具",
        "content": "今天发现了一个AI工具，感觉挺好用的，可以帮我写东西，也可以总结内容，大家可以试试。",
        "tags": ["AI", "工具"],
        "cover_text": "",
    }

    response = client.post("/api/diagnose/workflow", json=payload)

    assert response.status_code == 200
    body = response.json()
    problem_text = " ".join(body["problems"])
    all_issue_text = " ".join(issue for score in body["scores"] for issue in score["issues"])
    suggestion_text = " ".join(body["suggestions"])
    assert body["overall_score"] < 70
    assert "标题缺少数字或明确数量" in problem_text
    assert "正文信息量偏少" in all_issue_text
    assert "缺少评论区互动引导" in all_issue_text
    assert "步骤" in suggestion_text or "清单" in suggestion_text


@pytest.mark.parametrize(
    ("title", "content", "expected_terms"),
    [
        ("这个方法稳赚，百分百立刻见效", "照着做一定能变好，绝对不会失败。", ("稳赚", "百分百", "立刻见效", "一定能", "绝对")),
        ("私信领资料，加微信进群", "想要模板可以私信领，扫码后我发你。", ("私信领", "加微信", "扫码")),
        ("同款文案直接照抄", "这篇是转载搬运，复制原文就能用。", ("同款文案", "照抄", "转载", "搬运", "复制原文")),
    ],
)
def test_acceptance_risk_review_flags_more_high_risk_patterns(tmp_path, monkeypatch, title, content, expected_terms) -> None:
    monkeypatch.setenv("SAMPLE_DB_PATH", str(tmp_path / "samples.sqlite3"))
    payload = {
        "category": "内容创作",
        "target_audience": "内容创作者",
        "goal": "收藏",
        "title": title,
        "content": content,
        "tags": ["内容创作"],
        "cover_text": "",
    }

    response = client.post("/api/diagnose/workflow", json=payload)

    assert response.status_code == 200
    body = response.json()
    risk_text = " ".join(risk["message"] for risk in body["risks"])
    for term in expected_terms:
        assert term in risk_text
    assert any(risk["level"] in {"medium", "high"} for risk in body["risks"])


def test_cors_allows_vite_fallback_ports() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5176",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5176"


def test_cors_allows_frontend_origins_env(monkeypatch) -> None:
    from app.main import get_cors_origins

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("FRONTEND_ORIGINS", "https://demo.trycloudflare.com,https://demo.ngrok-free.app")

    origins = get_cors_origins()

    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5176" in origins
    assert "https://demo.trycloudflare.com" in origins
    assert "https://demo.ngrok-free.app" in origins
