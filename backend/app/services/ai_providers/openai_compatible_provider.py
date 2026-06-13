import json
import time
from typing import Any

import httpx

from app.services.ai_providers.base import AIClientError, AIProviderConfig
from app.services.ai_providers.json_utils import parse_json_object_from_text


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, config: AIProviderConfig) -> None:
        self.config = config

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.config.api_key:
            raise AIClientError("AI_API_KEY 未配置，无法调用兼容 OpenAI 的 AI Provider。")

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.config.max_tokens,
            "temperature": 0.2,
        }

        try:
            response = _post_with_retry(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                payload=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise AIClientError(_http_status_error_message(status_code, exc.response.text)) from exc
        except httpx.HTTPError as exc:
            raise AIClientError(f"AI Provider 请求失败，请检查网络或配置。底层错误：{type(exc).__name__}: {exc}") from exc

        return parse_json_object_from_text(self._extract_text(response.json()))

    def _extract_text(self, data: dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not isinstance(choices, list):
            raise AIClientError("AI Provider 返回缺少 choices。")

        fragments: list[str] = []
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            if choice.get("finish_reason") == "length":
                raise AIClientError(
                    f"AI Provider 输出被 max_tokens={self.config.max_tokens} 截断，请调高 AI_MAX_TOKENS。"
                )
            message = choice.get("message", {})
            if not isinstance(message, dict):
                continue
            fragments.extend(_content_to_text_fragments(message.get("content")))

        text = "".join(fragments).strip()
        if not text:
            raise AIClientError("AI Provider 返回为空。")
        return text


def _content_to_text_fragments(content: Any) -> list[str]:
    if isinstance(content, str):
        return [content]
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return [content["text"]]
        return [json.dumps(content, ensure_ascii=False)]
    if isinstance(content, list):
        fragments: list[str] = []
        for item in content:
            if isinstance(item, str):
                fragments.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    fragments.append(text)
                elif item.get("type") in {"text", "output_text"}:
                    fragments.append(json.dumps(item, ensure_ascii=False))
        return fragments
    return []


def _post_with_retry(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> httpx.Response:
    last_error: httpx.HTTPError | None = None
    for attempt in range(3):
        try:
            return httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError, httpx.ReadTimeout) as exc:
            last_error = exc
            if attempt == 2:
                break
            time.sleep(0.8 * (attempt + 1))
    if last_error:
        raise last_error
    raise AIClientError("AI Provider 请求未返回响应。")


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
