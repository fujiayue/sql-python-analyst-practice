from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


DB_PATH = Path(__file__).resolve().parents[1] / ".local" / "trainer.sqlite"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS progress (
                task_id TEXT PRIMARY KEY,
                passed INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_code TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                passed INTEGER NOT NULL,
                code TEXT NOT NULL,
                error_type TEXT,
                feedback TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS wrong_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                code TEXT NOT NULL,
                error_type TEXT,
                problem TEXT,
                reason TEXT,
                correct_code TEXT,
                business_explanation TEXT,
                reviewed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def get_progress_map() -> dict[str, dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM progress").fetchall()
    return {row["task_id"]: dict(row) for row in rows}


def record_attempt(task_id: str, mode: str, code: str, passed: bool, error_type: str | None, feedback: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO attempts(task_id, mode, passed, code, error_type, feedback) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, mode, int(passed), code, error_type, feedback),
        )
        current = conn.execute("SELECT attempts, passed FROM progress WHERE task_id = ?", (task_id,)).fetchone()
        if current:
            conn.execute(
                """
                UPDATE progress
                SET attempts = attempts + 1,
                    passed = CASE WHEN ? = 1 THEN 1 ELSE passed END,
                    last_code = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
                """,
                (int(passed), code, task_id),
            )
        else:
            conn.execute(
                "INSERT INTO progress(task_id, passed, attempts, last_code) VALUES (?, ?, 1, ?)",
                (task_id, int(passed), code),
            )
        if not passed:
            conn.execute(
                """
                INSERT INTO wrong_notes(task_id, code, error_type, problem, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, code, error_type, feedback, "待复盘：确认是语法、口径、连接重复、日期处理还是输出格式问题。"),
            )
        else:
            conn.execute(
                """
                UPDATE wrong_notes
                SET correct_code = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id FROM wrong_notes
                    WHERE task_id = ? AND (correct_code IS NULL OR correct_code = '')
                    ORDER BY created_at DESC
                    LIMIT 1
                )
                """,
                (code, task_id),
            )


def list_wrong_notes() -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM wrong_notes
            ORDER BY reviewed ASC, updated_at DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def mark_wrong_note_reviewed(note_id: int) -> bool:
    init_db()
    with _connect() as conn:
        result = conn.execute(
            """
            UPDATE wrong_notes
            SET reviewed = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (note_id,),
        )
        return result.rowcount > 0


def wrong_note_count() -> int:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM wrong_notes WHERE reviewed = 0").fetchone()
    return int(row["cnt"])
