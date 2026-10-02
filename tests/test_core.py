from __future__ import annotations

from pathlib import Path

from bot.auth import is_admin
from bot.broadcast import resolve_target_chat_ids
from bot.storage import Storage


def _storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.sqlite3")


def test_admin_authorization() -> None:
    admin_ids = frozenset({101, 202})
    assert is_admin(101, admin_ids)
    assert not is_admin(303, admin_ids)
    assert not is_admin(None, admin_ids)


def test_resolve_general_and_all_targets(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    storage.set_general_enabled(1, True)
    storage.set_general_enabled(2, False)
    storage.upsert_chat(-1001, "Ops", "supergroup", enabled=True)
    storage.upsert_chat(-1002, "Muted", "group", enabled=False)

    assert resolve_target_chat_ids(storage, "general") == [1]
    assert resolve_target_chat_ids(storage, "all") == [-1001, 1]


def test_resolve_specific_chat_target(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    assert resolve_target_chat_ids(storage, "chat:-100123") == [-100123]
