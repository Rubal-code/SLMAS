from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection

router = APIRouter(prefix="/admin", tags=["admin"])


class FeedbackRequest(BaseModel):
    task_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest):
    with get_connection() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (payload.task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        conn.execute(
            "UPDATE tasks SET metadata = ? WHERE id = ?",
            (str({"rating": payload.rating, "notes": payload.notes or ""}), payload.task_id),
        )
        conn.commit()

    return {
        "task_id": payload.task_id,
        "status": "feedback_received",
        "rating": payload.rating,
        "notes": payload.notes,
    }


@router.get("/feedback")
async def list_feedback():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, goal_text, metadata FROM tasks ORDER BY created_at DESC"
        ).fetchall()
    return {
        "feedback": [
            {"task_id": row["id"], "goal_text": row["goal_text"], "metadata": row["metadata"]}
            for row in rows
        ]
    }
