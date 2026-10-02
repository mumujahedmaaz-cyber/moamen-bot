# moamen-bot

Production-ready Telegram broadcast bot for admin-authored alerts/reminders.

## Features

- User-facing notification controls (menu buttons and commands):
  - Enable general notifications (private subscriber list)
  - Enable notifications for the current group/chat
  - Enable all notifications
  - Disable all notifications
- Admin-only broadcast controls:
  - `/broadcast <general|all|chat:CHAT_ID>` as a reply to any source message/media
  - `/admin_targets` to inspect known chats and subscriber counts
- Broadcast delivery uses `copyMessage`, allowing most Telegram message/media types to be forwarded while preserving captions/content where supported by Telegram.
- SQLite persistence for local/dev and easy deployment.
- Environment-based configuration with no hardcoded secrets.

## Security and release safety

- Secrets are read from environment variables only.
- `.env` and SQLite runtime files are ignored via `.gitignore`.
- Use `.env.example` as a template; never commit real secrets.
- Admin actions are guarded by Telegram user IDs in `ADMIN_IDS`.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your local `.env` from the example:

```bash
cp .env.example .env
```

4. Fill in:
   - `BOT_TOKEN`: token from BotFather
   - `ADMIN_IDS`: comma-separated Telegram user IDs allowed to use admin commands
   - `DATABASE_PATH` (optional): SQLite path (default: `data/bot.sqlite3`)
   - `LOG_LEVEL` (optional): e.g. `INFO`, `DEBUG`

## Run

```bash
python -m bot
```

## User commands/menu actions

- `/start`
- `/enable_general`
- `/enable_chat` (in a non-private chat)
- `/enable_all`
- `/disable_all`

Reply keyboard buttons perform the same actions.

## Admin commands

- `/broadcast <general|all|chat:CHAT_ID>`
  - Must be used as a reply to the source message/media to broadcast.
  - Targets:
    - `general`: private users with general notifications enabled
    - `chat:CHAT_ID`: one specific chat/group/channel id
    - `all`: union of general subscribers + enabled known chats
- `/admin_targets`

## Permissions and limitations

- Bot needs permission to post in target chats.
- Telegram API may reject inaccessible chats/users (blocked bot, removed membership, etc.). Failures are logged and skipped.
- `copyMessage` supports most message/media types, but some service/system messages cannot be copied by Bot API.
- Reply threading across different chats cannot be preserved by Telegram.

## Tests

Run:

```bash
pytest
```
