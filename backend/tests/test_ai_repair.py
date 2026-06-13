from app.services.ai_diagnosis_service import _generate_ai_content_with_repair
from app.services.ai_providers.base import AIInvalidJSONError


class RepairingClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, system_prompt, user_prompt):  # noqa: ANN001
        self.calls += 1
        if self.calls == 1:
            raise AIInvalidJSONError("AI Provider 返回内容不是有效 JSON。", raw_content="这是诊断：summary ok")
        return {
            "summary": "ok",
            "evidence_findings": [],
            "priority_actions": [],
            "problems": ["p"],
            "suggestions": ["s"],
            "rewritten_titles": ["a", "b", "c"],
            "optimized_body": "body",
            "recommended_tags": ["x", "y", "z"],
            "cover_text": ["cover"],
            "risks": [{"level": "low", "message": "ok"}],
        }


def test_generate_ai_content_repairs_invalid_json_once() -> None:
    client = RepairingClient()

    content = _generate_ai_content_with_repair(client, "system", "user")

    assert client.calls == 2
    assert content.summary == "ok"
    assert content.rewritten_titles == ["a", "b", "c"]
