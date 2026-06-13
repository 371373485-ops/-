import ast
import json
import re
from typing import Any

from app.services.ai_providers.base import AIClientError, AIInvalidJSONError


def parse_json_object_from_text(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content

    text = _normalize_text(str(content))
    if not text:
        raise AIClientError("AI Provider 返回为空。")

    candidates: list[str] = [text]
    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    candidates.extend(item.strip() for item in fenced if item.strip())
    candidates.extend(_extract_json_objects(text))
    for fenced_text in fenced:
        candidates.extend(_extract_json_objects(fenced_text))

    candidates.extend(_repair_json_like(candidate) for candidate in list(candidates))

    for candidate in _dedupe_candidates(candidates):
        parsed = _try_parse_object(candidate)
        if parsed is not None:
            return parsed

    raise AIInvalidJSONError("AI Provider 返回内容不是有效 JSON。", raw_content=text)


def _normalize_text(content: str) -> str:
    return (
        content.replace("\ufeff", "")
        .replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .strip()
    )


def _repair_json_like(text: str) -> str:
    repaired = text.strip()
    if repaired.lower().startswith("json\n"):
        repaired = repaired[5:].strip()
    repaired = (
        repaired.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    return repaired


def _try_parse_object(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        parsed = _try_raw_decode_object(candidate)
        if parsed is None:
            parsed = _try_python_literal_object(candidate)

    if parsed is None:
        return None
    if isinstance(parsed, dict):
        return parsed
    raise AIClientError("AI Provider 返回 JSON 结构不符合预期。")


def _try_raw_decode_object(text: str) -> Any | None:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"{", text):
        try:
            parsed, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _try_python_literal_object(text: str) -> Any | None:
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return None
    return parsed


def _extract_json_objects(text: str) -> list[str]:
    objects: list[str] = []

    for start_match in re.finditer(r"{", text):
        start = start_match.start()
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    objects.append(text[start : index + 1])
                    break
    return objects


def _dedupe_candidates(candidates: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique
