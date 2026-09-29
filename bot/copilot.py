from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import httpx


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class CopilotResponseError(ValueError):
    """Raised when the Copilot API returns an unexpected payload."""


class GitHubCopilotClient:
    def __init__(
        self,
        *,
        token: str,
        model: str,
        base_url: str,
        temperature: float,
        timeout: float = 60.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "discord-copilot-bot/1.0",
        }
        self._model = model
        self._temperature = temperature
        self._timeout = timeout

    async def create_response(self, messages: Sequence[ChatMessage]) -> str:
        payload = {
            "model": self._model,
            "temperature": self._temperature,
            "messages": [asdict(message) for message in messages],
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        return self._extract_text(data)

    def _extract_text(self, data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise CopilotResponseError("Copilot response does not contain choices.")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise CopilotResponseError("Copilot response choice is missing a message.")

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    text = item["text"].strip()
                    if text:
                        parts.append(text)
            if parts:
                return "\n".join(parts)

        raise CopilotResponseError("Copilot response message did not contain text.")
