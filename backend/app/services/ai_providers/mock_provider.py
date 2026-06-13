from typing import Any

from app.services.ai_providers.base import AIProviderConfig


class MockProvider:
    name = "mock"

    def __init__(self, config: AIProviderConfig) -> None:
        self.config = config

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return {
            "summary": "Mock Provider 模式：未调用真实外部模型，返回可用于联调的演示内容。",
            "problems": ["当前为 mock provider 输出，适合验证接口结构。"],
            "suggestions": ["如需真实 AI 输出，请配置真实 provider 和本地私有 API Key。"],
            "rewritten_titles": [
                "Mock 标题版本一",
                "Mock 标题版本二",
                "Mock 标题版本三",
            ],
            "optimized_body": "这是 mock provider 生成的正文占位内容，用于验证统一 Provider 架构。",
            "recommended_tags": ["mock", "接口联调", "演示"],
            "cover_text": ["Mock 封面文案"],
            "risks": [{"level": "low", "message": "Mock provider 未发现真实内容风险，发布前仍需人工复核。"}],
        }
