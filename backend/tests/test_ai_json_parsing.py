import pytest

from app.services.ai_providers.base import AIClientError
from app.services.ai_providers.json_utils import parse_json_object_from_text


def test_parse_json_object_accepts_plain_json() -> None:
    assert parse_json_object_from_text('{"summary":"ok"}') == {"summary": "ok"}


def test_parse_json_object_extracts_markdown_fenced_json() -> None:
    content = '```json\n{"summary":"ok","problems":["p"]}\n```'

    assert parse_json_object_from_text(content)["summary"] == "ok"


def test_parse_json_object_extracts_json_with_surrounding_text() -> None:
    content = '下面是结果：\n{"summary":"ok","nested":{"value":"} still string"}}\n请查收。'

    parsed = parse_json_object_from_text(content)

    assert parsed["summary"] == "ok"
    assert parsed["nested"]["value"] == "} still string"


def test_parse_json_object_rejects_non_object_json() -> None:
    with pytest.raises(AIClientError):
        parse_json_object_from_text('["not", "object"]')


def test_parse_json_object_repairs_trailing_commas_and_smart_quotes() -> None:
    content = "```json\n{“summary”: “ok”, “items”: [1, 2,],}\n```"

    parsed = parse_json_object_from_text(content)

    assert parsed == {"summary": "ok", "items": [1, 2]}
