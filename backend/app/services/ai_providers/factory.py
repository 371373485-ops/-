import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local convenience
    load_dotenv = None

from app.services.ai_providers.base import AIClientError, AIProviderClient, AIProviderConfig
from app.services.ai_providers.mock_provider import MockProvider
from app.services.ai_providers.openai_compatible_provider import OpenAICompatibleProvider
from app.services.ai_providers.openai_provider import OpenAIProvider


def _load_env() -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    if not load_dotenv:
        return
    load_dotenv()
    root_env = Path(__file__).resolve().parents[4] / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=False)


def get_ai_provider_config() -> AIProviderConfig:
    _load_env()
    provider = os.getenv("AI_PROVIDER", "openai").strip().lower() or "openai"
    api_key = os.getenv("AI_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    timeout_value = os.getenv("AI_TIMEOUT_SECONDS", "").strip() or os.getenv("OPENAI_TIMEOUT_SECONDS", "30").strip()
    max_tokens_value = os.getenv("AI_MAX_TOKENS", "").strip() or os.getenv("OPENAI_MAX_TOKENS", "4096").strip()
    base_url = os.getenv("AI_BASE_URL", "").strip() or "https://api.openai.com/v1"
    return AIProviderConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        timeout=float(timeout_value),
        base_url=base_url.rstrip("/"),
        max_tokens=int(max_tokens_value),
    )


def build_provider_client(config: AIProviderConfig) -> AIProviderClient:
    if config.provider == "mock":
        return MockProvider(config)
    if config.provider == "openai":
        return OpenAIProvider(config)
    if config.provider == "openai_compatible":
        return OpenAICompatibleProvider(config)
    raise AIClientError(f"暂不支持的 AI_PROVIDER：{config.provider}。")
