from app.services.ai_providers.json_utils import parse_json_object_from_text


def test_parse_json_object_skips_non_json_braces_before_result() -> None:
    content = '示例格式是 {不是: "json"}，正式结果如下：\n{"summary":"ok","items":[1,2]}'

    parsed = parse_json_object_from_text(content)

    assert parsed == {"summary": "ok", "items": [1, 2]}


def test_parse_json_object_accepts_python_style_object() -> None:
    parsed = parse_json_object_from_text("{'summary': 'ok', 'items': [1, 2,]}")

    assert parsed == {"summary": "ok", "items": [1, 2]}
