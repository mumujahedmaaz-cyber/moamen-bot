from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes


def is_admin(user_id: int | None, admin_ids: frozenset[int]) -> bool:
    return user_id in admin_ids if user_id is not None else False


def admin_only(handler: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(handler)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user = update.effective_user
        if not is_admin(user.id if user else None, context.bot_data["admin_ids"]):
            if update.effective_message:
                await update.effective_message.reply_text("This action is restricted to bot admins.")
            return None
        return await handler(update, context, *args, **kwargs)

    return wrapped
