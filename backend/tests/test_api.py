import pytest
from fastapi.testclient import TestClient

from app.agents.body_rewrite_agent import BodyRewriteAgent
from app.main import app
from app.services.ai_client import AIClientError, OpenAIClient
from app.services.ai_providers.factory import build_provider_client, get_ai_provider_config
from app.services.ai_providers.mock_provider import MockProvider
from app.services.ai_providers.openai_compatible_provider import OpenAICompatibleProvider
from app.services.ai_providers.openai_provider import OpenAIProvider


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_sample_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAMPLE_DB_PATH", str(tmp_path / "samples.sqlite3"))


def _diagnosis_payload(**overrides):
    payload = {
        "title": "新手护肤避坑清单！",
        "content": "第一，我会先看成分和肤质。第二，我会记录真实体验。最后，欢迎在评论区交流。",
        "category": "护肤",
        "target_audience": "护肤新手",
        "goal": "收藏",
        "tags": ["护肤", "新手", "避坑清单"],
        "cover_text": "新手护肤先看",
    }
    payload.update(overrides)
    return payload


def _csv_upload(text: str):
    return {
        "file": ("samples.csv", text.encode("utf-8-sig"), "text/csv"),
    }


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rule_diagnosis_accepts_frontend_chinese_goal() -> None:
    response = client.post("/api/diagnose/rule", json=_diagnosis_payload())

    body = response.json()
    assert response.status_code == 200
    assert body["mode"] == "rule"
    assert 0 <= body["overall_score"] <= 100
    assert len(body["scores"]) == 9
    assert {item["key"] for item in body["scores"]} == {
        "title_score",
        "opening_score",
        "structure_score",
        "emotion_score",
        "value_score",
        "interaction_score",
        "tag_score",
        "style_score",
        "conversion_score",
    }


def test_rule_diagnosis_returns_evidence_based_findings() -> None:
    payload = _diagnosis_payload(
        title="护肤怎么做",
        content="这个护肤方法挺好用，大家可以试试。",
        category="护肤",
        target_audience="护肤新手",
        goal="收藏",
        tags=["护肤"],
        cover_text="护肤笔记",
    )

    response = client.post("/api/diagnose/rule", json=payload)

    body = response.json()
    raw = response.text
    assert response.status_code == 200
    assert body["diagnosis_id"]
    assert body["category"] == "护肤"
    assert len(body["top_3_blockers"]) <= 3
    assert body["top_3_blockers"]
    assert body["evidence_based_issues"]
    evidence_issue = body["evidence_based_issues"][0]
    assert {
        "field",
        "original_excerpt",
        "issue",
        "why_it_matters",
        "impact_area",
        "severity",
        "rewrite_principle",
        "example_fix",
    } <= set(evidence_issue)
    assert evidence_issue["impact_area"] in {"click", "completion", "trust", "interaction", "compliance"}
    assert evidence_issue["severity"] in {"low", "medium", "high"}
    assert body["reader_reaction_simulation"]["title_first_impression"]
    assert body["reader_reaction_simulation"]["after_first_three_lines"]
    assert body["reader_reaction_simulation"]["likely_drop_off_reason"]
    assert body["reader_reaction_simulation"]["strongest_interest_point"]
    assert body["reader_reaction_simulation"]["information_to_frontload"]
    assert body["structure_analysis"]["opening_hook"]
    assert body["structure_analysis"]["information_hierarchy"]
    assert body["structure_analysis"]["trust_building"]
    assert body["structure_analysis"]["detail_evidence"]
    assert body["structure_analysis"]["emotional_resonance"]
    assert body["structure_analysis"]["action_guidance"]
    assert isinstance(body["credibility_review"]["is_too_generic"], bool)
    assert isinstance(body["credibility_review"]["sounds_like_ad"], bool)
    assert body["missing_user_inputs"]
    assert body["rewritten_versions"]["titles"]
    assert body["rewritten_versions"]["body"]
    assert body["rewrite_explanations"]
    assert body["risk_review"]["overall_level"] in {"low", "medium", "high"}
    assert body["ai_disclosure_notice"]
    assert body["evidence_findings"]
    assert body["priority_actions"]
    first = body["evidence_findings"][0]
    assert first["priority"].startswith("P")
    assert first["evidence"]
    assert first["issue"]
    assert first["impact"]
    assert first["action"]
    assert any("点击" in item["dimension"] or "完读" in item["dimension"] for item in body["evidence_findings"])
    assert "增强吸引力" not in raw
    assert "优化表达" not in raw
    assert "突出卖点" not in raw


def test_mock_and_ai_mock_diagnosis_are_available(monkeypatch) -> None:
    mock_response = client.post("/api/diagnose/mock", json=_diagnosis_payload())
    assert mock_response.status_code == 200
    mock_body = mock_response.json()
    assert mock_body["rewritten_titles"]
    assert mock_body["evidence_findings"]
    assert mock_body["priority_actions"]

    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ai_response = client.post("/api/diagnose/ai", json=_diagnosis_payload())
    assert ai_response.status_code == 200
    assert ai_response.json()["mode"] == "ai_mock"


def test_ai_status_does_not_expose_api_key(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_AI", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-should-not-leak")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)

    response = client.get("/api/diagnose/ai/status")

    assert response.status_code == 200
    body = response.json()
    raw = response.text
    assert body["use_mock_ai"] is False
    assert body["provider"] == "openai"
    assert body["openai_configured"] is True
    assert body["provider_configured"] is True
    assert body["real_ai_ready"] is True
    assert body["mode"] == "real_ai"
    assert "test-secret-should-not-leak" not in raw


def test_ai_provider_factory_supports_mock_and_openai(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = get_ai_provider_config()
    assert config.provider == "mock"
    assert config.is_configured is True
    assert isinstance(build_provider_client(config), MockProvider)

    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "test-secret-should-not-leak")
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("AI_BASE_URL", "https://api.openai.com/v1")
    config = get_ai_provider_config()
    assert config.provider == "openai"
    assert config.api_key == "test-secret-should-not-leak"
    assert config.model == "gpt-4o-mini"
    assert isinstance(build_provider_client(config), OpenAIProvider)

    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_API_KEY", "test-secret-should-not-leak")
    monkeypatch.setenv("AI_BASE_URL", "https://example-model.test/v1")
    monkeypatch.setenv("AI_MODEL", "compatible-chat")
    config = get_ai_provider_config()
    assert config.provider == "openai_compatible"
    assert config.base_url == "https://example-model.test/v1"
    assert isinstance(build_provider_client(config), OpenAICompatibleProvider)


def test_openai_compatible_provider_uses_chat_completions(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok","problems":["p"],"suggestions":["s"],"rewritten_titles":["a","b","c"],"optimized_body":"body","recommended_tags":["x","y","z"],"cover_text":["cover"],"risks":[{"level":"low","message":"ok"}]}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):  # noqa: ANN001
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.services.ai_providers.openai_compatible_provider.httpx.post", fake_post)
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_API_KEY", "test-secret-should-not-leak")
    monkeypatch.setenv("AI_BASE_URL", "https://example-model.test/v1")
    monkeypatch.setenv("AI_MODEL", "compatible-chat")

    provider = build_provider_client(get_ai_provider_config())
    result = provider.generate_json("system", "user")

    assert result["summary"] == "ok"
    assert captured["url"] == "https://example-model.test/v1/chat/completions"
    assert captured["json"]["model"] == "compatible-chat"
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert "test-secret-should-not-leak" not in str(captured["json"])


def test_ai_diagnosis_failure_falls_back_without_key_leak(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_AI", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-should-not-leak")

    def fail_generate_json(self, system_prompt, user_prompt):  # noqa: ANN001
        raise AIClientError("OpenAI API 请求失败，状态码：401。")

    monkeypatch.setattr(OpenAIClient, "generate_json", fail_generate_json)

    response = client.post("/api/diagnose/ai", json=_diagnosis_payload())

    assert response.status_code == 200
    body = response.json()
    raw = response.text
    assert body["mode"] == "ai_fallback"
    assert body["rewritten_titles"]
    assert body["scores"]
    assert "OpenAI API 请求失败" in raw
    assert "401" in raw
    assert "test-secret-should-not-leak" not in raw


def test_ai_diagnosis_preserves_rule_scores_and_evidence_fields(monkeypatch) -> None:
    payload = _diagnosis_payload(
        title="护肤怎么做",
        content="这个护肤方法挺好用，大家可以试试。",
        tags=["护肤"],
        cover_text="护肤笔记",
    )
    rule_body = client.post("/api/diagnose/rule", json=payload).json()

    monkeypatch.setenv("USE_MOCK_AI", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-should-not-leak")

    def fake_generate_json(self, system_prompt, user_prompt):  # noqa: ANN001
        assert "不重新计算 overall_score" in user_prompt
        assert "不覆盖规则生成的 diagnosis_sources" in user_prompt
        assert "不编造真实经历" in user_prompt
        assert "优化表达、增强吸引力、突出卖点、提升内容质量" in system_prompt
        return {
            "overall_score": 100,
            "diagnosis_sources": [],
            "score_deductions": [],
            "evidence_diagnosis": [],
            "reader_perspectives": [],
            "revision_tasks": [],
            "evidence_findings": [],
            "priority_actions": [],
            "summary": "AI 只润色摘要，不改规则证据。",
            "problems": ["正文缺少真实场景证据，需要补充【请补充真实场景】。"],
            "suggestions": ["在原文“大家可以试试”后补充真实使用周期和不适用情况。"],
            "rewritten_titles": ["护肤新手先看这3个检查点", "护肤方法别急着照搬", "护肤前先确认这些边界"],
            "optimized_body": "这个方法只适合作为经验模板：【请补充真实使用周期】【请补充观察到的变化】【请补充不适用情况】。",
            "recommended_tags": ["护肤", "护肤新手", "经验分享"],
            "cover_text": ["护肤前先自查"],
            "risks": [{"level": "low", "message": "未发现高风险表达。"}],
        }

    monkeypatch.setattr(OpenAIClient, "generate_json", fake_generate_json)

    response = client.post("/api/diagnose/ai", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["mode"] == "ai"
    assert body["overall_score"] == rule_body["overall_score"]
    assert body["diagnosis_sources"] == rule_body["diagnosis_sources"]
    assert body["score_deductions"] == rule_body["score_deductions"]
    assert body["evidence_diagnosis"] == rule_body["evidence_diagnosis"]
    assert body["reader_perspectives"] == rule_body["reader_perspectives"]
    assert body["revision_tasks"] == rule_body["revision_tasks"]
    assert body["evidence_findings"] == rule_body["evidence_findings"]
    assert body["priority_actions"] == rule_body["priority_actions"]
    assert body["summary"] == "AI 只润色摘要，不改规则证据。"
    assert body["optimized_body"] != rule_body["optimized_body"]


def test_rule_and_workflow_detect_high_risk_terms() -> None:
    payload = _diagnosis_payload(title="保证变好！加微信领取全网最好方案", content="这篇绝对有效，私信领资料。")

    rule_response = client.post("/api/diagnose/rule", json=payload)
    assert rule_response.status_code == 200
    rule_body = rule_response.json()
    assert rule_body["risk_review"]["risk_level"] == "high"
    assert rule_body["risk_review"]["human_review_required"] is True
    assert rule_body["risk_review"]["risk_items"]
    assert rule_body["risk_review"]["safe_alternatives"]
    assert rule_body["rewritten_titles"] == []

    workflow_response = client.post("/api/diagnose/workflow", json=payload)
    body = workflow_response.json()
    assert workflow_response.status_code == 200
    assert body["risk_review"]["risk_level"] == "high"
    assert body["risk_review"]["human_review_required"] is True
    assert any("绝对化表达" in risk["risk_type"] or "站外引流" in risk["risk_type"] for risk in body["risk_review"]["risk_items"])
    assert any("避免虚假宣传" in suggestion or "站内评论区" in suggestion for suggestion in body["suggestions"])
    assert body["rewritten_titles"] == []


def test_import_samples_csv_and_list() -> None:
    csv_text = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "新手护肤清单,第一步先看肤质,\"护肤,新手\",护肤,120,80,12,新手先看,2026-01-01,系统生成的虚构演示样本,demo_generated\n"
    )

    import_response = client.post("/api/samples/import", files=_csv_upload(csv_text))
    assert import_response.status_code == 200
    imported = import_response.json()
    assert imported["imported_count"] == 1
    assert imported["samples"][0]["source_type"] == "demo_generated"

    list_response = client.get("/api/samples")
    body = list_response.json()
    assert list_response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["category"] == "护肤"


def test_samples_list_filters_and_detail_and_delete() -> None:
    csv_text = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "护肤样本,护肤内容,\"护肤,清单\",护肤,10,5,1,护肤封面,,用户自有账号手动整理,own_account_manual\n"
        "穿搭样本,穿搭内容,\"穿搭,通勤\",穿搭,20,8,2,穿搭封面,,授权样本手动整理,authorized_manual\n"
    )
    client.post("/api/samples/import", files=_csv_upload(csv_text))

    filtered = client.get("/api/samples", params={"category": "穿搭", "source_type": "authorized_manual"})
    assert filtered.status_code == 200
    items = filtered.json()["items"]
    assert len(items) == 1
    sample_id = items[0]["id"]

    detail = client.get(f"/api/samples/{sample_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "穿搭样本"

    deleted = client.delete(f"/api/samples/{sample_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    missing = client.get(f"/api/samples/{sample_id}")
    assert missing.status_code == 404


def test_import_rejects_invalid_source_type_and_missing_source_type() -> None:
    invalid_csv = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "样本,内容,标签,护肤,1,1,1,封面,,来源说明,unknown_source\n"
    )
    invalid_response = client.post("/api/samples/import", files=_csv_upload(invalid_csv))
    assert invalid_response.status_code == 400
    assert "source_type 无效" in invalid_response.json()["detail"]

    missing_csv = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note\n"
        "样本,内容,标签,护肤,1,1,1,封面,,来源说明\n"
    )
    missing_response = client.post("/api/samples/import", files=_csv_upload(missing_csv))
    assert missing_response.status_code == 400
    assert "source_type" in missing_response.json()["detail"]


def test_import_rejects_invalid_numeric_and_oversized_csv() -> None:
    invalid_numeric = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "样本,内容,标签,护肤,很多,1,1,封面,,来源说明,own_account_manual\n"
    )
    response = client.post("/api/samples/import", files=_csv_upload(invalid_numeric))
    assert response.status_code == 400
    assert "likes 必须是非负整数" in response.json()["detail"]

    large_content = "a" * 1_000_001
    large_response = client.post("/api/samples/import", files=_csv_upload(large_content))
    assert large_response.status_code == 400
    assert "CSV 文件过大" in large_response.json()["detail"]


def test_pattern_analysis_by_category_and_empty_library() -> None:
    empty = client.get("/api/patterns/analyze")
    assert empty.status_code == 200
    assert empty.json()["insufficient_sample_warning"] == "样本量不足，分析仅供参考。"

    csv_text = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "护肤新手先看这 3 个避坑点,先说结论，护肤新手先看肤质,\"护肤,新手,避坑\",护肤,100,60,10,护肤避坑,,演示样本,demo_generated\n"
        "护肤清单收藏版,我真实踩坑后整理的护肤清单,\"护肤,清单,收藏\",护肤,200,150,20,收藏清单,,演示样本,demo_generated\n"
    )
    client.post("/api/samples/import", files=_csv_upload(csv_text))

    response = client.get("/api/patterns/analyze", params={"category": "护肤"})
    body = response.json()
    assert response.status_code == 200
    assert body["category"] == "护肤"
    assert body["sample_count"] == 2
    assert body["average_likes"] == 150
    assert any(item["name"] == "数字型" for item in body["title_structures"])
    assert any(item["name"] == "结论先行" for item in body["opening_structures"])


def test_similar_case_match_returns_top_cases_and_caution() -> None:
    csv_text = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "护肤新手先看这 3 个避坑点,第一步先看肤质，第二步对比成分，最后收藏总结,\"护肤,新手,避坑清单\",护肤,300,200,40,护肤避坑,,演示样本,demo_generated\n"
        "护肤清单收藏版,真实踩坑后整理的护肤清单,\"护肤,清单,收藏\",护肤,180,130,18,收藏清单,,演示样本,demo_generated\n"
        "护肤步骤教程,给护肤新手的步骤方法,\"护肤,新手,教程\",护肤,120,70,9,护肤教程,,演示样本,demo_generated\n"
    )
    client.post("/api/samples/import", files=_csv_upload(csv_text))

    response = client.post("/api/cases/match", json=_diagnosis_payload(title="护肤新手别错过这 3 个避坑方法"))
    body = response.json()
    assert response.status_code == 200
    assert len(body["matched_samples"]) == 3
    assert body["matched_samples"][0]["category"] == "护肤"
    assert "仅供结构参考" in body["matched_samples"][0]["caution"]
    assert "赛道相同" in body["matched_samples"][0]["similarity_reason"]


def test_similar_case_match_empty_and_no_similar_samples() -> None:
    empty = client.post("/api/cases/match", json=_diagnosis_payload())
    assert empty.status_code == 200
    assert empty.json()["matched_samples"] == []
    assert "样本库为空" in empty.json()["message"]

    csv_text = (
        "title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type\n"
        "通勤穿搭教程,给上班族的穿搭步骤,\"穿搭,通勤,教程\",穿搭,80,30,5,通勤教程,,演示样本,demo_generated\n"
    )
    client.post("/api/samples/import", files=_csv_upload(csv_text))
    no_similar = client.post("/api/cases/match", json=_diagnosis_payload())
    assert no_similar.status_code == 200
    assert no_similar.json()["matched_samples"] == []
    assert "暂未找到足够相似" in no_similar.json()["message"]


def test_workflow_diagnosis_returns_multi_agent_report_and_saves_history() -> None:
    response = client.post("/api/diagnose/workflow", json=_diagnosis_payload())
    body = response.json()
    assert response.status_code == 200
    assert body["mode"] == "workflow"
    assert len(body["rewritten_titles"]) == 5
    assert body["optimized_body"]
    assert body["recommended_tags"]
    assert body["comment_guides"]

    history = client.get("/api/history")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["title"] == "新手护肤避坑清单！"


def test_workflow_diagnosis_survives_agent_failure(monkeypatch) -> None:
    def broken_run(self, agent_input):
        raise RuntimeError("body rewrite failed")

    monkeypatch.setattr(BodyRewriteAgent, "run", broken_run)

    response = client.post("/api/diagnose/workflow", json=_diagnosis_payload())

    body = response.json()
    assert response.status_code == 200
    assert body["mode"] == "workflow"
    assert any("BodyRewriteAgent 执行失败" in problem for problem in body["problems"])


def test_history_detail_markdown_export_and_delete() -> None:
    client.post("/api/diagnose/workflow", json=_diagnosis_payload())
    history_id = client.get("/api/history").json()["items"][0]["id"]

    detail = client.get(f"/api/history/{history_id}")
    assert detail.status_code == 200
    assert detail.json()["input"]["title"] == "新手护肤避坑清单！"
    assert detail.json()["output"]["overall_score"] >= 0

    exported = client.get(f"/api/history/{history_id}/export")
    assert exported.status_code == 200
    body = exported.json()
    assert body["filename"] == f"diagnosis-report-{history_id}.md"
    assert "# 小红书爆款内容诊断报告" in body["markdown"]
    assert "## 证据型诊断" in body["markdown"]
    assert "## 优先改法" in body["markdown"]
    assert "## 相似案例" in body["markdown"]
    assert "## 风险审查" in body["markdown"]

    deleted = client.delete(f"/api/history/{history_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    missing = client.get(f"/api/history/{history_id}")
    assert missing.status_code == 404
