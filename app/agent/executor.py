import json
from typing import Any, Dict, Optional

from app.agent.tools import mock_db, mock_search
from app.db import get_task, get_next_pending_step, update_step_status, update_task_status


def execute_step(task_id: str) -> Dict[str, Any]:
    task = get_task(task_id)
    if not task:
        raise ValueError("Task not found")

    next_step = get_next_pending_step(task_id)
    if not next_step:
        update_task_status(task_id, "completed", "No pending steps left.")
        return {"task_id": task_id, "status": "completed", "message": "No pending steps left."}

    description = next_step["description"]
    tool_name = "mock_search"
    if "database" in description.lower() or "db" in description.lower():
        tool_name = "mock_db"

    if tool_name == "mock_db":
        result = mock_db(task_id)
    else:
        result = mock_search(description)

    update_step_status(next_step["id"], "completed", json.dumps({"tool": tool_name, "result": result}))

    remaining = get_next_pending_step(task_id)
    if remaining is None:
        update_task_status(task_id, "completed", json.dumps({"last_step": description, "tool_result": result}))
        status = "completed"
    else:
        update_task_status(task_id, "running", json.dumps({"last_step": description, "tool_result": result}))
        status = "running"

    return {
        "task_id": task_id,
        "status": status,
        "executed_step": description,
        "tool": tool_name,
        "result": result,
    }
