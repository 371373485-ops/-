from app.services.ai_providers.base import AIProviderConfig
from app.services.ai_providers.base import AIClientError
from app.services.ai_providers.openai_compatible_provider import OpenAICompatibleProvider
from app.services.ai_providers.openai_provider import OpenAIProvider


def _config(provider: str = "openai") -> AIProviderConfig:
    return AIProviderConfig(
        provider=provider,
        api_key="test-key",
        model="test-model",
        timeout=30,
        base_url="https://example.test/v1",
        max_tokens=4096,
    )


def test_openai_compatible_extracts_array_content() -> None:
    provider = OpenAICompatibleProvider(_config("openai_compatible"))
    data = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": '{"summary":"ok",'},
                        {"type": "text", "text": '"items":[1]}'},
                    ]
                }
            }
        ]
    }

    assert provider._extract_text(data) == '{"summary":"ok","items":[1]}'


def test_openai_responses_extracts_structured_text_object() -> None:
    provider = OpenAIProvider(_config())
    data = {
        "output": [
            {
                "content": [
                    {
                        "type": "output_text",
                        "text": {"summary": "ok", "items": [1]},
                    }
                ]
            }
        ]
    }

    assert provider._extract_text(data) == '{"summary": "ok", "items": [1]}'


def test_openai_compatible_reports_truncated_output() -> None:
    provider = OpenAICompatibleProvider(_config("openai_compatible"))
    data = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {"content": '{"summary":"cut off"'},
            }
        ]
    }

    try:
        provider._extract_text(data)
    except AIClientError as exc:
        assert "截断" in str(exc)
        assert "AI_MAX_TOKENS" in str(exc)
    else:
        raise AssertionError("Expected truncated output to raise AIClientError")


def test_openai_responses_reports_incomplete_output() -> None:
    provider = OpenAIProvider(_config())
    data = {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}

    try:
        provider._extract_text(data)
    except AIClientError as exc:
        assert "AI_MAX_TOKENS" in str(exc)
    else:
        raise AssertionError("Expected incomplete output to raise AIClientError")
