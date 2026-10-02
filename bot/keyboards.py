from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup

ENABLE_GENERAL_TEXT = "✅ Enable general notifications"
ENABLE_CHAT_TEXT = "✅ Enable notifications for this chat"
ENABLE_ALL_TEXT = "🔔 Enable all notifications"
DISABLE_ALL_TEXT = "🔕 Disable all notifications"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(ENABLE_GENERAL_TEXT)],
            [KeyboardButton(ENABLE_CHAT_TEXT)],
            [KeyboardButton(ENABLE_ALL_TEXT), KeyboardButton(DISABLE_ALL_TEXT)],
        ],
        resize_keyboard=True,
    )
