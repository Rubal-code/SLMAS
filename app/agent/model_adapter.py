import json
import os
import unicodedata
from typing import List

import requests


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def generate_steps_from_goal(goal_text: str) -> List[str]:
    groq_key = _get_env("GROQ_API_KEY")
    groq_url = _get_env("GROQ_API_URL", "https://api.groq.com/openai/v1")
    groq_model = _get_env("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not groq_key:
        return fallback_steps(goal_text)

    system_prompt = (
        "You are a planning assistant. Break the user goal into clear short steps. "
        "Return only a numbered list with 3 to 6 steps. Use concise action phrases."
    )
    user_prompt = f"Goal: {goal_text}"

    try:
        response = requests.post(
            f"{groq_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": groq_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        steps = parse_steps(content)
        if steps:
            return steps
    except Exception:
        pass

    return fallback_steps(goal_text)


def parse_steps(content: str) -> List[str]:
    if not content:
        return []
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    cleaned = []
    for line in lines:
        text = _normalize_text(line.strip())
        if text.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            text = text.split(".", 1)[1].strip() if "." in text else text
        elif text.startswith("- "):
            text = text[2:].strip()
        elif text.startswith("* "):
            text = text[2:].strip()
        if text:
            cleaned.append(text)
    return cleaned[:6]


def fallback_steps(goal_text: str) -> List[str]:
    goal = _normalize_text(goal_text.strip())
    if not goal:
        return ["Understand the task and define the objective."]
    return [
        f"Clarify the objective behind: {goal}",
        "Break the task into smaller actionable sub-steps.",
        "Execute the highest-priority action and validate the result.",
        "Review outcomes and refine before completing the task.",
    ]
