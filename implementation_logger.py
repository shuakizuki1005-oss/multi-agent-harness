import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

def create_implementation_log(task, repo_path, branch_name):
    return {
        "task": task,
        "repository": str(repo_path),
        "branch": branch_name,
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "history": [],
        "status": "RUNNING"
    }

def add_log_entry(log_data, attempt, test_passed, test_output,review_passed, review, repair_attempted):
    log_data["history"].append({
        "attempt": attempt,
        "test_passed": test_passed,
        "test_output": test_output,
        "review_passed": review_passed,
        "review": review,
        "repair_attempted": repair_attempted
    })

def save_implementation_log(log_data, status):
    log_data["status"] = status
    log_data["finished_at"] = datetime.now().isoformat()

    log_dir = Path(__file__).resolve().parent / "logs" / "implementation"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = uuid4().hex[:8]

    log_path = log_dir / f"run-{timestamp}-{unique_id}.json"

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(
            log_data,
            file,
            ensure_ascii=False,
            indent=2
        )

        return log_path