from typing import List

from app.agent.model_adapter import generate_steps_from_goal


def plan_task_steps(goal_text: str) -> List[str]:
    return generate_steps_from_goal(goal_text)
