import sqlite3

import pytest

from scripts.manage import backup_database, restore_database


def test_backup_restore_consistency(client, cfg, tmp_path):
    backup = tmp_path / "backup.db"
    assert backup_database(cfg.db_path, backup)["bytes"] > 0
    restored = tmp_path / "restored.db"
    info = restore_database(backup, restored)
    assert info["counts"]["participants"] == 12
    with sqlite3.connect(restored) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    with pytest.raises(ValueError, match="never overwritten"):
        restore_database(backup, restored)


def test_invalid_backup_does_not_create_target(tmp_path):
    invalid = tmp_path / "other.db"
    with sqlite3.connect(invalid) as conn:
        conn.execute("CREATE TABLE other(id)")
    target = tmp_path / "target.db"
    with pytest.raises(ValueError, match="complete conference"):
        restore_database(invalid, target)
    assert not target.exists()
