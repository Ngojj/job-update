"""Ghi nhớ các job đã gửi để không báo trùng (file JSON commit được lên git)."""
import json
import os
from datetime import datetime, timedelta

SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "seen_jobs.json")


def load_seen() -> dict:
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_seen(seen: dict, retention_days: int = 60) -> None:
    cutoff = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    pruned = {k: v for k, v in seen.items() if v >= cutoff}
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(pruned, f, ensure_ascii=False, indent=0, sort_keys=True)


def mark_seen(seen: dict, job_id: str) -> None:
    seen[job_id] = datetime.now().strftime("%Y-%m-%d")
