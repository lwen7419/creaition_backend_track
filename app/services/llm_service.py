import anthropic

from app.config import settings

DEFAULT_MAX_TOKENS = 16000

anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class LLMService:
    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system

        response = self._client.messages.create(**kwargs)
        return next((block.text for block in response.content if block.type == "text"), "")


llm_service = LLMService(anthropic_client, settings.anthropic_model)


def get_llm_service() -> LLMService:
    return llm_service
