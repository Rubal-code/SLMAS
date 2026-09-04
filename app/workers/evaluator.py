import json
from pathlib import Path
from typing import Any, Dict, List

from app.db import get_connection

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "golden_examples.jsonl"


def evaluate_task(task_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return {"task_id": task_id, "status": "not_found"}

        steps = conn.execute(
            "SELECT * FROM task_steps WHERE task_id = ? ORDER BY step_index ASC",
            (task_id,),
        ).fetchall()

        completed = sum(1 for step in steps if step["status"] == "completed")
        total = len(steps)
        success = completed > 0 and total > 0
        score = round((completed / total) * 100, 2) if total else 0.0

        result = {
            "task_id": task_id,
            "goal_text": task["goal_text"],
            "status": "success" if success else "needs_attention",
            "completed_steps": completed,
            "total_steps": total,
            "score": score,
        }

        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DATA_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "task_id": task_id,
                "goal_text": task["goal_text"],
                "completed_steps": completed,
                "total_steps": total,
                "score": score,
                "status": result["status"],
            }) + "\n")

        return result


def run_evaluation_for_all_tasks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        task_rows = conn.execute("SELECT id FROM tasks ORDER BY created_at DESC").fetchall()
    return [evaluate_task(row["id"]) for row in task_rows]
