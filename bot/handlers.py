from __future__ import annotations

import logging

from telegram import Message, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.auth import admin_only
from bot.broadcast import copy_with_backoff, resolve_target_chat_ids
from bot.keyboards import (
    DISABLE_ALL_TEXT,
    ENABLE_ALL_TEXT,
    ENABLE_CHAT_TEXT,
    ENABLE_GENERAL_TEXT,
    main_menu_keyboard,
)
from bot.storage import Storage

logger = logging.getLogger(__name__)


def _storage(context: ContextTypes.DEFAULT_TYPE) -> Storage:
    return context.bot_data["storage"]


def _chat_title(message: Message) -> str:
    chat = message.chat
    return chat.title or chat.full_name or str(chat.id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    if update.effective_chat and update.effective_chat.type != "private":
        _storage(context).upsert_chat(
            chat_id=update.effective_chat.id,
            title=_chat_title(message),
            chat_type=update.effective_chat.type,
            enabled=True,
        )

    await message.reply_text(
        "Use the menu to control notifications.",
        reply_markup=main_menu_keyboard(),
    )


async def enable_general(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.effective_message:
        return
    _storage(context).set_general_enabled(update.effective_user.id, True)
    await update.effective_message.reply_text("General notifications are now enabled.")


async def enable_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.effective_message.reply_text("Run this action inside the target group/chat.")
        return

    _storage(context).upsert_chat(
        chat_id=chat.id,
        title=_chat_title(update.effective_message),
        chat_type=chat.type,
        enabled=True,
    )
    await update.effective_message.reply_text("Notifications for this chat are now enabled.")


async def enable_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await enable_general(update, context)
    if update.effective_chat and update.effective_chat.type != "private":
        await enable_chat(update, context)


async def disable_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    if update.effective_user:
        _storage(context).set_general_enabled(update.effective_user.id, False)

    chat = update.effective_chat
    if chat and chat.type != "private":
        existing = _storage(context).get_chat(chat.id)
        if existing:
            _storage(context).set_chat_enabled(chat.id, False)

    await update.effective_message.reply_text("All notifications are now disabled for this context.")


async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    handlers = {
        ENABLE_GENERAL_TEXT: enable_general,
        ENABLE_CHAT_TEXT: enable_chat,
        ENABLE_ALL_TEXT: enable_all,
        DISABLE_ALL_TEXT: disable_all,
    }

    callback = handlers.get(message.text)
    if callback:
        await callback(update, context)


async def track_known_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or chat.type == "private":
        return

    _storage(context).upsert_chat(
        chat_id=chat.id,
        title=_chat_title(message),
        chat_type=chat.type,
        enabled=True,
    )


@admin_only
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    if not context.args:
        await message.reply_text("Usage: /broadcast <general|all|chat:CHAT_ID> (must reply to a message)")
        return

    if not message.reply_to_message:
        await message.reply_text("Reply to the source message/media you want to broadcast.")
        return

    target = context.args[0]
    try:
        recipients = resolve_target_chat_ids(_storage(context), target)
    except ValueError as exc:
        await message.reply_text(str(exc))
        return

    if not recipients:
        await message.reply_text("No recipients found for the selected target.")
        return

    success_count = 0
    failure_count = 0
    source_chat_id = message.reply_to_message.chat_id
    source_message_id = message.reply_to_message.message_id

    for chat_id in recipients:
        if await copy_with_backoff(context, chat_id, source_chat_id, source_message_id):
            success_count += 1
        else:
            failure_count += 1

    logger.info(
        "Broadcast done by %s target=%s success=%s failure=%s",
        update.effective_user.id if update.effective_user else "unknown",
        target,
        success_count,
        failure_count,
    )
    await message.reply_text(
        f"Broadcast complete. Sent: {success_count}, failed: {failure_count}."
    )


@admin_only
async def admin_list_targets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    users = _storage(context).list_general_subscribers()
    chats = _storage(context).list_known_chats()

    lines = [
        f"General subscribers: {len(users)}",
        "Known chats:",
    ]
    if chats:
        for chat in chats:
            lines.append(
                f"- {chat.title} ({chat.chat_id}, {chat.chat_type}) enabled={chat.enabled}"
            )
    else:
        lines.append("- none")

    await message.reply_text("\n".join(lines))


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("enable_general", enable_general))
    application.add_handler(CommandHandler("enable_chat", enable_chat))
    application.add_handler(CommandHandler("enable_all", enable_all))
    application.add_handler(CommandHandler("disable_all", disable_all))

    application.add_handler(CommandHandler("broadcast", admin_broadcast))
    application.add_handler(CommandHandler("admin_targets", admin_list_targets))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_known_chat), group=1)
