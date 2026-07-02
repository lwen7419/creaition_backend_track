import anthropic

from src.config import settings

DEFAULT_MAX_TOKENS = 16000

anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

EXTRACT_TASK_TOOL = {
    "name": "extract_task",
    "description": "Extract a structured task from natural language text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "A short, clear title for the task.",
            },
            "description": {
                "type": "string",
                "description": "Additional details about the task, if any were given.",
            },
            "due_date": {
                "type": "string",
                "description": (
                    "The task's due date in YYYY-MM-DD format, if one was mentioned or "
                    "implied. Resolve relative dates (e.g. 'tomorrow', 'next Friday') "
                    "using the reference date given in the system prompt."
                ),
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "The task's priority. Default to 'medium' if not indicated.",
            },
        },
        "required": ["title"],
        "additionalProperties": False,
    },
    "strict": True,
}

SUGGEST_TAGS_TOOL = {
    "name": "suggest_tags",
    "description": "Suggest relevant tags for a task based on its title and description.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "description": (
                    "Between 2 and 4 short, lowercase tags (single words or short "
                    "phrases) relevant to the task."
                ),
                "items": {"type": "string"},
            },
        },
        "required": ["tags"],
        "additionalProperties": False,
    },
    "strict": True,
}

RECOMMEND_PRIORITY_TOOL = {
    "name": "recommend_priority",
    "description": "Recommend a priority level for a task based on its title and description.",
    "input_schema": {
        "type": "object",
        "properties": {
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "The recommended priority level.",
            },
        },
        "required": ["priority"],
        "additionalProperties": False,
    },
    "strict": True,
}


def _task_content(title: str, description: str | None) -> str:
    content = f"Title: {title}"
    if description:
        content += f"\nDescription: {description}"
    return content


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

    def extract_task(self, text: str, *, reference_date: str) -> dict:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=f"Today's date is {reference_date}.",
            tools=[EXTRACT_TASK_TOOL],
            tool_choice={"type": "tool", "name": "extract_task"},
            messages=[{"role": "user", "content": text}],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return tool_use.input

    def suggest_tags(self, title: str, description: str | None = None) -> list[str]:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=256,
            system="Suggest between 2 and 4 short, relevant tags for the given task.",
            tools=[SUGGEST_TAGS_TOOL],
            tool_choice={"type": "tool", "name": "suggest_tags"},
            messages=[{"role": "user", "content": _task_content(title, description)}],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return list(tool_use.input.get("tags", []))[:4]

    def recommend_priority(self, title: str, description: str | None = None) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=256,
            system="Recommend a priority level (low, medium, or high) for the given task.",
            tools=[RECOMMEND_PRIORITY_TOOL],
            tool_choice={"type": "tool", "name": "recommend_priority"},
            messages=[{"role": "user", "content": _task_content(title, description)}],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return tool_use.input["priority"]


llm_service = LLMService(anthropic_client, settings.anthropic_model)


def get_llm_service() -> LLMService:
    return llm_service
