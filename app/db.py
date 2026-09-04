import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "agent.sqlite"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                goal_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                result TEXT DEFAULT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_steps (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                step_index INTEGER NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                result TEXT DEFAULT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """
        )

        cols = conn.execute("PRAGMA table_info(task_steps)").fetchall()
        col_names = {row[1] for row in cols}
        if "result" not in col_names:
            conn.execute("ALTER TABLE task_steps ADD COLUMN result TEXT DEFAULT NULL")
        conn.commit()


def create_task(goal_text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    task_id = uuid4().hex
    now = utc_now_iso()
    data = metadata or {}

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks (id, goal_text, status, created_at, updated_at, metadata)
            VALUES (?, ?, 'pending', ?, ?, ?)
            """,
            (task_id, goal_text, now, now, str(data)),
        )
        conn.execute(
            """
            INSERT INTO task_steps (id, task_id, step_index, description, status, created_at, updated_at)
            VALUES (?, ?, 0, 'Receive goal and initialize task', 'completed', ?, ?)
            """,
            (uuid4().hex, task_id, now, now),
        )
        conn.commit()

    return get_task(task_id)


def add_task_steps(task_id: str, steps: List[str]) -> None:
    if not steps:
        return

    with get_connection() as conn:
        existing_count = conn.execute(
            "SELECT COUNT(*) FROM task_steps WHERE task_id = ?",
            (task_id,),
        ).fetchone()[0]

        now = utc_now_iso()
        for index, description in enumerate(steps, start=existing_count):
            conn.execute(
                """
                INSERT INTO task_steps (id, task_id, step_index, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (uuid4().hex, task_id, index, description, now, now),
            )
        conn.commit()


def update_task_status(task_id: str, status: str, result: Optional[str] = None) -> None:
    now = utc_now_iso()
    with get_connection() as conn:
        if result is None:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, task_id),
            )
        else:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, result = ? WHERE id = ?",
                (status, now, result, task_id),
            )
        conn.commit()


def get_next_pending_step(task_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM task_steps WHERE task_id = ? AND status = 'pending' ORDER BY step_index ASC LIMIT 1",
            (task_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "task_id": row["task_id"],
            "step_index": row["step_index"],
            "description": row["description"],
            "status": row["status"],
        }


def update_step_status(step_id: str, status: str, result: Optional[str] = None) -> None:
    now = utc_now_iso()
    with get_connection() as conn:
        if result is None:
            conn.execute(
                "UPDATE task_steps SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, step_id),
            )
        else:
            conn.execute(
                "UPDATE task_steps SET status = ?, updated_at = ?, result = ? WHERE id = ?",
                (status, now, result, step_id),
            )
        conn.commit()


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        task_row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if not task_row:
            return None

        steps = conn.execute(
            "SELECT * FROM task_steps WHERE task_id = ? ORDER BY step_index ASC",
            (task_id,),
        ).fetchall()

        return {
            "task_id": task_row["id"],
            "goal_text": task_row["goal_text"],
            "status": task_row["status"],
            "created_at": task_row["created_at"],
            "updated_at": task_row["updated_at"],
            "metadata": _parse_json(task_row["metadata"]),
            "status_message": task_row["result"],
            "steps": [
                {
                    "id": step["id"],
                    "step_index": step["step_index"],
                    "description": step["description"],
                    "status": step["status"],
                    "created_at": step["created_at"],
                    "updated_at": step["updated_at"],
                }
                for step in steps
            ],
        }


def list_tasks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "task_id": row["id"],
                "goal_text": row["goal_text"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": _parse_json(row["metadata"]),
            }
            for row in rows
        ]


def _parse_json(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        import json
        return json.loads(raw)
    except Exception:
        return {}
