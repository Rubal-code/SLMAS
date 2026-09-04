import json
from typing import Any, Dict, List


def mock_search(query: str) -> Dict[str, Any]:
    q = (query or "").strip().lower()
    samples = {
        "self-learning": [
            "Self-learning systems improve from prior experiences using feedback loops.",
            "Memory and retrieval help an agent reuse successful patterns.",
        ],
        "ai agent": [
            "AI agents combine planning, tools, and memory to solve tasks.",
            "A planner decomposes work into smaller steps for execution.",
        ],
        "default": [
            "The task requires a structured plan and validation loop.",
            "Use a safe execution path and review results before finalizing.",
        ],
    }
    matches = samples.get(q, samples["default"])
    return {
        "tool": "mock_search",
        "query": query,
        "results": matches,
    }


def mock_db(task_id: str) -> Dict[str, Any]:
    return {
        "tool": "mock_db",
        "task_id": task_id,
        "summary": {
            "status": "ready",
            "records": 1,
            "last_updated": "now",
        },
        "notes": ["Task exists and is ready for execution.", "Execution result should be logged for learning."],
    }
