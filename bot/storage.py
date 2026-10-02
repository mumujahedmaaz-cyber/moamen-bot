from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnownChat:
    chat_id: int
    title: str
    chat_type: str
    enabled: bool


class Storage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    general_enabled INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS chat_subscriptions (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    chat_type TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def set_general_enabled(self, user_id: int, enabled: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_subscriptions (user_id, general_enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    general_enabled = excluded.general_enabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, int(enabled)),
            )

    def is_general_enabled(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT general_enabled FROM user_subscriptions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return bool(row["general_enabled"]) if row else False

    def upsert_chat(self, chat_id: int, title: str, chat_type: str, enabled: bool = True) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_subscriptions (chat_id, title, chat_type, enabled, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(chat_id) DO UPDATE SET
                    title = excluded.title,
                    chat_type = excluded.chat_type,
                    enabled = excluded.enabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, title, chat_type, int(enabled)),
            )

    def set_chat_enabled(self, chat_id: int, enabled: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE chat_subscriptions SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (int(enabled), chat_id),
            )

    def get_chat(self, chat_id: int) -> KnownChat | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT chat_id, title, chat_type, enabled FROM chat_subscriptions WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        if not row:
            return None
        return KnownChat(
            chat_id=row["chat_id"],
            title=row["title"],
            chat_type=row["chat_type"],
            enabled=bool(row["enabled"]),
        )

    def list_general_subscribers(self) -> list[int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT user_id FROM user_subscriptions WHERE general_enabled = 1"
            ).fetchall()
        return [int(row["user_id"]) for row in rows]

    def list_enabled_chats(self) -> list[KnownChat]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT chat_id, title, chat_type, enabled
                FROM chat_subscriptions
                WHERE enabled = 1
                ORDER BY title COLLATE NOCASE, chat_id
                """
            ).fetchall()

        return [
            KnownChat(
                chat_id=row["chat_id"],
                title=row["title"],
                chat_type=row["chat_type"],
                enabled=bool(row["enabled"]),
            )
            for row in rows
        ]

    def list_known_chats(self) -> list[KnownChat]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT chat_id, title, chat_type, enabled
                FROM chat_subscriptions
                ORDER BY title COLLATE NOCASE, chat_id
                """
            ).fetchall()

        return [
            KnownChat(
                chat_id=row["chat_id"],
                title=row["title"],
                chat_type=row["chat_type"],
                enabled=bool(row["enabled"]),
            )
            for row in rows
        ]
