from typing import List

from app.agent.memory import MemoryStore
from app.agent.model_adapter import generate_steps_from_goal


def plan_task_steps(goal_text: str) -> List[str]:
    memory_store = MemoryStore()
    similar = memory_store.get_similar(goal_text, limit=3)
    context = []
    for item in similar:
        goal = item.get("goal_text", "")
        steps = item.get("steps", [])
        if goal:
            context.append(goal)
        context.extend([str(step) for step in steps])
    return generate_steps_from_goal(goal_text, context)
