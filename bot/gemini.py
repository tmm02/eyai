from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Sequence

import httpx


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class GeminiResponseError(ValueError):
    """Raised when the Gemini API returns an unexpected payload."""


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        temperature: float,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._temperature = temperature
        self._timeout = timeout

    async def create_response(
        self, *, system_prompt: str, messages: Sequence[ChatMessage]
    ) -> str:
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [self._to_gemini_content(message) for message in messages],
            "generationConfig": {
                "temperature": self._temperature,
            },
        }

        retries = 3
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        (
                            f"{self._base_url}/models/"
                            f"{self._model}:generateContent?key={self._api_key}"
                        ),
                        json=payload,
                    )
                    response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if status not in {429, 500, 502, 503, 504} or attempt == retries:
                    raise
                await self._sleep_before_retry(attempt)
                continue

            data = response.json()
            return self._extract_text(data)

        raise GeminiResponseError("Gemini request failed after retries.")

    async def _sleep_before_retry(self, attempt: int) -> None:
        delay = 2 ** attempt
        await asyncio.sleep(delay)

    def _to_gemini_content(self, message: ChatMessage) -> dict[str, Any]:
        role = "model" if message.role == "assistant" else "user"
        return {
            "role": role,
            "parts": [{"text": message.content}],
        }

    def _extract_text(self, data: dict[str, Any]) -> str:
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise GeminiResponseError("Gemini response does not contain candidates.")

        content = candidates[0].get("content")
        if not isinstance(content, dict):
            raise GeminiResponseError("Gemini response candidate is missing content.")

        parts = content.get("parts")
        if not isinstance(parts, list):
            raise GeminiResponseError("Gemini response content is missing parts.")

        texts: list[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())

        if texts:
            return "\n".join(texts)

        finish_reason = candidates[0].get("finishReason")
        if finish_reason == "SAFETY":
            raise GeminiResponseError("Gemini blocked the response for safety reasons.")

        raise GeminiResponseError("Gemini response did not contain text.")
