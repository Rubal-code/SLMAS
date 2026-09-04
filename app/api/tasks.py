from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.planner import plan_task_steps
from app.db import add_task_steps, create_task, get_task, list_tasks, update_task_status

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreateRequest(BaseModel):
    goal_text: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


@router.post("", status_code=201)
async def create_task_endpoint(payload: TaskCreateRequest):
    task = create_task(payload.goal_text, payload.metadata)
    plan_steps = plan_task_steps(payload.goal_text)
    if plan_steps:
        add_task_steps(task["task_id"], plan_steps)
        update_task_status(task["task_id"], "planned")
    task = get_task(task["task_id"])
    return task


@router.get("")
async def list_task_endpoint():
    return {"tasks": list_tasks()}


@router.get("/{task_id}")
async def get_task_endpoint(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
