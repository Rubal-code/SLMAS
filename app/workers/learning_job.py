import json
from pathlib import Path
from typing import List, Dict

from app.workers.evaluator import run_evaluation_for_all_tasks

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "learning_summary.json"


def build_learning_summary() -> Dict[str, Any]:
    evaluations = run_evaluation_for_all_tasks()
    summary = {
        "total_tasks": len(evaluations),
        "successful_tasks": sum(1 for item in evaluations if item.get("status") == "success"),
        "needs_attention": sum(1 for item in evaluations if item.get("status") == "needs_attention"),
        "average_score": round(
            sum(float(item.get("score", 0.0)) for item in evaluations) / len(evaluations),
            2,
        ) if evaluations else 0.0,
        "evaluations": evaluations,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_learning_job() -> Dict[str, Any]:
    return build_learning_summary()
