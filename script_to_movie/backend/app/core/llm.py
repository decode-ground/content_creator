import json
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self):
        self._client: anthropic.AsyncAnthropic | None = None

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def invoke(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        anthropic_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        kwargs: dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
        }

        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)

        if response.content and len(response.content) > 0:
            return response.content[0].text
        return ""

    async def invoke_structured(
        self,
        messages: list[dict[str, str]],
        output_schema: type[T],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> T:
        schema = output_schema.model_json_schema()
        schema_name = output_schema.__name__

        tool_definition = {
            "name": schema_name,
            "description": f"Output structured data matching {schema_name} schema",
            "input_schema": schema,
        }

        anthropic_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        kwargs: dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
            "tools": [tool_definition],
            "tool_choice": {"type": "tool", "name": schema_name},
        }

        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)

        for block in response.content:
            if block.type == "tool_use" and block.name == schema_name:
                return output_schema.model_validate(block.input)

        raise ValueError(f"No structured output received for {schema_name}")

    async def invoke_json(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        enhanced_system = (system or "") + "\n\nRespond with valid JSON only, no other text."

        response = await self.invoke(
            messages=messages,
            system=enhanced_system,
            max_tokens=max_tokens,
        )

        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())


llm_client = LLMClient()
