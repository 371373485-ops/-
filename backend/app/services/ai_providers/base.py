from dataclasses import dataclass
from typing import Any, Protocol


class AIClientError(Exception):
    """Raised when an external AI request fails or returns invalid data."""


class AIInvalidJSONError(AIClientError):
    """Raised when provider text cannot be parsed as a JSON object."""

    def __init__(self, message: str, raw_content: str) -> None:
        super().__init__(message)
        self.raw_content = raw_content


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    api_key: str
    model: str
    timeout: float
    base_url: str
    max_tokens: int

    @property
    def is_configured(self) -> bool:
        return self.provider == "mock" or bool(self.api_key)


class AIProviderClient(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        ...
