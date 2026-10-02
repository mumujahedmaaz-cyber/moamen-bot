from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    database_path: Path
    log_level: str


def _parse_admin_ids(raw_admin_ids: str) -> frozenset[int]:
    parsed: set[int] = set()
    for chunk in raw_admin_ids.split(","):
        cleaned = chunk.strip()
        if not cleaned:
            continue
        parsed.add(int(cleaned))
    return frozenset(parsed)


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is required")

    raw_admin_ids = os.getenv("ADMIN_IDS", "").strip()
    if not raw_admin_ids:
        raise ValueError("ADMIN_IDS is required and must contain at least one Telegram user id")

    admin_ids = _parse_admin_ids(raw_admin_ids)
    if not admin_ids:
        raise ValueError("ADMIN_IDS must contain at least one Telegram user id")

    database_path = Path(os.getenv("DATABASE_PATH", "data/bot.sqlite3")).expanduser().resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        database_path=database_path,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
