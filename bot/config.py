from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _parse_channel_ids(raw_value: str) -> tuple[int, ...]:
    ids: list[int] = []

    for chunk in raw_value.split(","):
        value = chunk.strip()
        if not value:
            continue
        if not value.isdigit():
            raise ValueError(
                "AI_CHANNEL_IDS must contain only Discord channel IDs separated by commas."
            )
        ids.append(int(value))

    if not ids:
        raise ValueError("AI_CHANNEL_IDS must contain at least one Discord channel ID.")

    return tuple(ids)


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    gemini_api_key: str
    gemini_model: str
    gemini_base_url: str
    ai_channel_ids: tuple[int, ...]
    max_history_messages: int
    response_temperature: float
    system_prompt: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        discord_bot_token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        if not discord_bot_token:
            raise ValueError("DISCORD_BOT_TOKEN is required.")

        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required.")

        raw_channel_ids = os.getenv("AI_CHANNEL_IDS", "").strip()
        if not raw_channel_ids:
            raise ValueError("AI_CHANNEL_IDS is required.")

        raw_history = os.getenv("MAX_HISTORY_MESSAGES", "12").strip()
        if not raw_history.isdigit():
            raise ValueError("MAX_HISTORY_MESSAGES must be a positive integer.")

        max_history_messages = int(raw_history)
        if max_history_messages <= 0:
            raise ValueError("MAX_HISTORY_MESSAGES must be greater than zero.")

        raw_temperature = os.getenv("RESPONSE_TEMPERATURE", "0.7").strip()
        try:
            response_temperature = float(raw_temperature)
        except ValueError as exc:
            raise ValueError("RESPONSE_TEMPERATURE must be a valid number.") from exc

        if not 0 <= response_temperature <= 2:
            raise ValueError("RESPONSE_TEMPERATURE must be between 0 and 2.")

        system_prompt = os.getenv(
            "SYSTEM_PROMPT",
            (
                "Kamu adalah AI assistant untuk server Discord ini. "
                "Jawab dengan ramah, jelas, dan tetap relevan dengan percakapan."
            ),
        ).strip()
        if not system_prompt:
            raise ValueError("SYSTEM_PROMPT must not be empty.")

        return cls(
            discord_bot_token=discord_bot_token,
            gemini_api_key=gemini_api_key,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
            or "gemini-3.8-flash",
            gemini_base_url=os.getenv(
                "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
            ).rstrip("/"),
            ai_channel_ids=_parse_channel_ids(raw_channel_ids),
            max_history_messages=max_history_messages,
            response_temperature=response_temperature,
            system_prompt=system_prompt,
        )
