import json
from pathlib import Path
from typing import Any, Dict, List

MEMORY_PATH = Path(__file__).resolve().parents[2] / "data" / "memory.json"


class MemoryStore:
    def __init__(self, path: Path | None = None):
        self.path = path or MEMORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
                return payload if isinstance(payload, list) else []
        except Exception:
            return []

    def _save(self, items: List[Dict[str, Any]]) -> None:
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(items, fh, indent=2)

    def save_experience(self, task_id: str, goal_text: str, steps: List[str], result: Any = None) -> Dict[str, Any]:
        items = self._load()
        item = {
            "task_id": task_id,
            "goal_text": goal_text,
            "steps": steps,
            "result": result,
            "score": 1.0 if result else 0.5,
        }
        items.append(item)
        self._save(items)
        return item

    def get_similar(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        text = (query or "").lower().strip()
        if not text:
            return []

        items = self._load()
        scored = []
        for item in items:
            full_text = " ".join([str(item.get("goal_text", "")), *[str(s) for s in item.get("steps", [])], str(item.get("result", ""))]).lower()
            score = 0
            for word in text.split():
                if word in full_text:
                    score += 1
            if score > 0:
                scored.append({"score": score, "item": item})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return [entry["item"] for entry in scored[:limit]]
