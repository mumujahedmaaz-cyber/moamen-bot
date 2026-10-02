from __future__ import annotations

import asyncio
import logging

from telegram.error import BadRequest, Forbidden, NetworkError, RetryAfter, TimedOut
from telegram.ext import ContextTypes

from bot.storage import Storage

logger = logging.getLogger(__name__)


def resolve_target_chat_ids(storage: Storage, target: str) -> list[int]:
    normalized = target.strip().lower()
    if normalized == "general":
        return storage.list_general_subscribers()
    if normalized == "all":
        users = storage.list_general_subscribers()
        chats = [chat.chat_id for chat in storage.list_enabled_chats()]
        return sorted(set(users + chats))
    if normalized.startswith("chat:"):
        chat_id = int(normalized.split(":", maxsplit=1)[1])
        return [chat_id]
    raise ValueError("Unsupported target. Use one of: general, all, chat:<chat_id>")


async def copy_with_backoff(
    context: ContextTypes.DEFAULT_TYPE,
    to_chat_id: int,
    from_chat_id: int,
    message_id: int,
    *,
    max_attempts: int = 4,
) -> bool:
    for attempt in range(1, max_attempts + 1):
        try:
            await context.bot.copy_message(
                chat_id=to_chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
            return True
        except RetryAfter as exc:
            wait_seconds = int(exc.retry_after) + 1
            logger.warning("Rate limited while sending to %s, waiting %ss", to_chat_id, wait_seconds)
            await asyncio.sleep(wait_seconds)
        except (TimedOut, NetworkError) as exc:
            if attempt == max_attempts:
                logger.error("Network error while sending to %s: %s", to_chat_id, exc)
                return False
            await asyncio.sleep(min(attempt * 2, 8))
        except (Forbidden, BadRequest) as exc:
            logger.warning("Skipping target %s due to Telegram API rejection: %s", to_chat_id, exc)
            return False
    return False
