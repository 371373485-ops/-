import json
from typing import Any

import httpx

from app.services.ai_providers.base import AIClientError, AIProviderConfig
from app.services.ai_providers.json_utils import parse_json_object_from_text


class OpenAIProvider:
    name = "openai"

    def __init__(self, config: AIProviderConfig) -> None:
        self.config = config

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.config.api_key:
            raise AIClientError("AI_API_KEY 或 OPENAI_API_KEY 未配置，无法调用真实 AI。")

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "text": {
                "format": {
                    "type": "json_object",
                }
            },
            "max_output_tokens": self.config.max_tokens,
            "temperature": 0.2,
        }

        try:
            response = httpx.post(
                f"{self.config.base_url}/responses",
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise AIClientError(_http_status_error_message(status_code, exc.response.text)) from exc
        except httpx.HTTPError as exc:
            raise AIClientError("AI Provider 请求失败，请检查网络或配置。") from exc

        return parse_json_object_from_text(self._extract_text(response.json()))

    def _extract_text(self, data: dict[str, Any]) -> str:
        if data.get("status") == "incomplete":
            reason = data.get("incomplete_details", {}).get("reason", "unknown")
            raise AIClientError(
                f"AI Provider 输出未完成，原因：{reason}。请调高 AI_MAX_TOKENS 或检查模型输出限制。"
            )

        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        if isinstance(data.get("output_text"), dict):
            return json.dumps(data["output_text"], ensure_ascii=False)

        output = data.get("output", [])
        fragments: list[str] = []
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", [])
                if isinstance(content, dict):
                    content = [content]
                if not isinstance(content, list):
                    continue
                for content_item in content:
                    fragments.extend(_response_content_to_text_fragments(content_item))

        content = "".join(fragments).strip()
        if not content:
            raise AIClientError("AI Provider 返回为空。")
        return content


def _response_content_to_text_fragments(content_item: Any) -> list[str]:
    if isinstance(content_item, str):
        return [content_item]
    if not isinstance(content_item, dict):
        return []

    text = content_item.get("text")
    if isinstance(text, str):
        return [text]
    if isinstance(text, dict):
        return [json.dumps(text, ensure_ascii=False)]

    if content_item.get("type") in {"output_text", "text"}:
        return [json.dumps(content_item, ensure_ascii=False)]
    return []


def _http_status_error_message(status_code: int, response_text: str) -> str:
    detail = response_text.strip().replace("\n", " ")[:300]
    if status_code == 429:
        message = "AI Provider 返回 429：请求过于频繁、额度不足或当前模型限流。"
    elif status_code in {401, 403}:
        message = "AI Provider 鉴权失败，请检查 API Key、模型权限或账号额度。"
    else:
        message = f"AI Provider 请求失败，状态码：{status_code}。"
    if detail:
        return f"{message} Provider 响应：{detail}"
    return message
