import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local convenience
    load_dotenv = None

if load_dotenv:
    load_dotenv()
    root_env = Path(__file__).resolve().parents[3] / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=False)

from app.services.ai_providers.base import AIClientError
from app.services.ai_providers.factory import build_provider_client, get_ai_provider_config


class OpenAIClient:
    """Compatibility facade for the existing diagnosis service and tests."""

    def __init__(self) -> None:
        self.config = get_ai_provider_config()
        self.provider = self.config.provider
        self.api_key = self.config.api_key
        self.model = self.config.model
        self.timeout = self.config.timeout
        self.base_url = self.config.base_url

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return build_provider_client(self.config).generate_json(system_prompt, user_prompt)


def should_use_mock_ai() -> bool:
    value = os.getenv("USE_MOCK_AI", "true").strip().lower()
    return value in {"1", "true", "yes", "on"}
