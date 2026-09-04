import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings

MEMORY_PATH = Path(__file__).resolve().parents[2] / "data" / "memory.json"


def _text_to_vector(text: str, size: int = 32) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    values: List[float] = []
    for i in range(size):
        chunk = digest[(i * 2) % len(digest): (i * 2 + 8) % len(digest) or len(digest)]
        value = int(chunk or "0", 16) / float(0xFFFFFF + 1)
        values.append(round(value, 6))
    return values


class MemoryStore:
    def __init__(self, path: Path | None = None):
        self.path = path or MEMORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

        self.use_qdrant = False
        self.qdrant_client = None
        self.collection_name = settings.qdrant_collection

        try:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
            self.use_qdrant = True
            self.qdrant_client.get_collection(self.collection_name)
        except Exception:
            self.use_qdrant = False
            self.qdrant_client = None

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
        item = {
            "task_id": task_id,
            "goal_text": goal_text,
            "steps": steps,
            "result": result,
            "score": 1.0 if result else 0.5,
        }

        if self.use_qdrant and self.qdrant_client is not None:
            try:
                from qdrant_client.http import models
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=32, distance=models.Distance.COSINE),
                )
            except Exception:
                pass
            try:
                payload = {"task_id": task_id, "goal_text": goal_text, "steps": steps, "result": str(result) if result else ""}
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        {
                            "id": task_id,
                            "vector": _text_to_vector(goal_text + " " + " ".join(steps)),
                            "payload": payload,
                        }
                    ],
                )
            except Exception:
                pass

        items = self._load()
        items.append(item)
        self._save(items)
        return item

    def get_similar(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        text = (query or "").lower().strip()
        if not text:
            return []

        if self.use_qdrant and self.qdrant_client is not None:
            try:
                hits = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=_text_to_vector(text),
                    limit=limit,
                )
                results = []
                for hit in hits:
                    payload = getattr(hit, "payload", {}) or {}
                    if payload:
                        results.append(payload)
                if results:
                    return results
            except Exception:
                pass

        items = self._load()
        scored = []
        for item in items:
            full_text = " ".join([
                str(item.get("goal_text", "")),
                *[str(s) for s in item.get("steps", [])],
                str(item.get("result", "")),
            ]).lower()
            score = 0
            for word in text.split():
                if word in full_text:
                    score += 1
            if score > 0:
                scored.append({"score": score, "item": item})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return [entry["item"] for entry in scored[:limit]]
