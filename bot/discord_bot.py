from __future__ import annotations

import logging
from collections import defaultdict, deque
from collections.abc import Iterable

import discord
import httpx

from bot.config import Settings
from bot.gemini import ChatMessage, GeminiClient, GeminiResponseError

LOGGER = logging.getLogger(__name__)
DISCORD_MESSAGE_LIMIT = 2000


class ConversationStore:
    def __init__(self, max_history_messages: int) -> None:
        self._entries: dict[str, deque[ChatMessage]] = defaultdict(
            lambda: deque(maxlen=max_history_messages)
        )

    def get(self, key: str) -> list[ChatMessage]:
        return list(self._entries[key])

    def append(self, key: str, message: ChatMessage) -> None:
        self._entries[key].append(message)


class DiscordAiBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True

        super().__init__(intents=intents)

        self.settings = settings
        self.conversations = ConversationStore(settings.max_history_messages)
        self.gemini = GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            base_url=settings.gemini_base_url,
            temperature=settings.response_temperature,
        )

    async def on_ready(self) -> None:
        if self.user is None:
            raise RuntimeError("Discord bot user is unavailable after login.")

        LOGGER.info("Logged in as %s (%s)", self.user, self.user.id)

    async def on_message(self, message: discord.Message) -> None:
        if self.user is None:
            raise RuntimeError("Discord bot user is unavailable during message handling.")

        if message.author.bot or message.author.id == self.user.id:
            return

        prompt = await self._build_prompt(message)
        if prompt is None:
            return

        history_key = self._history_key(message)
        messages = [
            *self.conversations.get(history_key),
            ChatMessage(role="user", content=prompt),
        ]

        async with message.channel.typing():
            try:
                response_text = await self.gemini.create_response(
                    system_prompt=self.settings.system_prompt,
                    messages=messages,
                )
            except httpx.HTTPStatusError as exc:
                LOGGER.error(
                    "Gemini HTTP error %s: %s", exc.response.status_code, exc.response.text
                )
                await message.reply(
                    "Aku gagal menghubungi Gemini API. Cek API key, model, atau endpoint-nya ya.",
                    mention_author=False,
                )
                return
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                LOGGER.error("Gemini network error: %s", exc)
                await message.reply(
                    "Koneksi ke Gemini sedang bermasalah. Coba lagi sebentar ya.",
                    mention_author=False,
                )
                return
            except GeminiResponseError as exc:
                LOGGER.error("Gemini payload error: %s", exc)
                await message.reply(
                    "Balasan dari Gemini tidak bisa diproses. Cek konfigurasi model atau endpoint.",
                    mention_author=False,
                )
                return

        self.conversations.append(history_key, ChatMessage(role="user", content=prompt))
        self.conversations.append(
            history_key, ChatMessage(role="assistant", content=response_text)
        )

        for chunk in _split_message(response_text):
            await message.reply(chunk, mention_author=False)

    async def _build_prompt(self, message: discord.Message) -> str | None:
        if self.user is None:
            raise RuntimeError("Discord bot user is unavailable while building prompt.")

        in_ai_channel = message.channel.id in self.settings.ai_channel_ids
        mention_trigger = self.user.mentioned_in(message)
        referenced_bot_message = await self._get_referenced_bot_message(message)
        reply_trigger = referenced_bot_message is not None

        if not in_ai_channel and not mention_trigger and not reply_trigger:
            return None

        clean_content = message.content
        if mention_trigger:
            clean_content = clean_content.replace(self.user.mention, "").replace(
                f"<@!{self.user.id}>", ""
            )

        clean_content = clean_content.strip()
        attachment_text = _format_attachments(message.attachments)

        if clean_content and attachment_text:
            body = f"{clean_content}\n\n{attachment_text}"
        elif clean_content:
            body = clean_content
        elif attachment_text:
            body = attachment_text
        else:
            return None

        if in_ai_channel:
            body = f"{message.author.display_name}: {body}"

        if referenced_bot_message is not None and referenced_bot_message.content.strip():
            return (
                "Balasan bot yang sedang ditanggapi:\n"
                f"{referenced_bot_message.content.strip()}\n\n"
                f"Pesan pengguna:\n{body}"
            )

        return body

    async def _get_referenced_bot_message(
        self, message: discord.Message
    ) -> discord.Message | None:
        if self.user is None or message.reference is None:
            return None

        if isinstance(message.reference.resolved, discord.Message):
            if message.reference.resolved.author.id == self.user.id:
                return message.reference.resolved
            return None

        if message.reference.message_id is None:
            return None

        try:
            referenced_message = await message.channel.fetch_message(
                message.reference.message_id
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
            LOGGER.warning("Unable to fetch referenced message: %s", exc)
            return None

        if referenced_message.author.id == self.user.id:
            return referenced_message
        return None

    def _history_key(self, message: discord.Message) -> str:
        if message.channel.id in self.settings.ai_channel_ids:
            return f"channel:{message.channel.id}"
        return f"channel:{message.channel.id}:user:{message.author.id}"


def _format_attachments(attachments: Iterable[discord.Attachment]) -> str:
    lines = [f"Attachment: {attachment.filename} ({attachment.url})" for attachment in attachments]
    if not lines:
        return ""
    return "\n".join(lines)


def _split_message(content: str) -> list[str]:
    if len(content) <= DISCORD_MESSAGE_LIMIT:
        return [content]

    chunks: list[str] = []
    remaining = content

    while len(remaining) > DISCORD_MESSAGE_LIMIT:
        split_at = remaining.rfind("\n", 0, DISCORD_MESSAGE_LIMIT)
        if split_at == -1:
            split_at = DISCORD_MESSAGE_LIMIT
        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def run_bot() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    settings = Settings.from_env()
    DiscordAiBot(settings).run(settings.discord_bot_token)
