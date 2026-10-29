import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

LOG_DIR = Path(__file__).resolve().parent / "logs"

def save_log(task, repo_path, plan, history, status):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now().astimezone()
    filename = f"{now:%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.json"
    log_path = LOG_DIR / filename
    
    log_data = {
        "timestamp": now.isoformat(),
        "repository": str(repo_path),
        "task": task,
        "initial_plan": plan,
        "history": history,
        "final_plan": history[-1]["plan"] if history else plan,
        "status": status
    }

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(log_data, file, ensure_ascii=False, indent=4)

    return log_path