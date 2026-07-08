import json
import os
from pathlib import Path

# Vercel /tmp là writable duy nhất trong serverless
DATA_FILE = "/tmp/users.json"

def _load() -> dict:
    Path("data").mkdir(exist_ok=True)
    if not Path(DATA_FILE).exists():
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id: int) -> dict:
    data = _load()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "points": 0,
            "total_earned": 0,
            "tasks_done": 0,
            "pending_withdraw": 0,
            "withdraw_history": []
        }
        _save(data)
    return data[uid]

def update_user(user_id: int, updates: dict):
    data = _load()
    uid = str(user_id)
    if uid not in data:
        get_user(user_id)
        data = _load()
    data[uid].update(updates)
    _save(data)

def add_points(user_id: int, points: int):
    user = get_user(user_id)
    update_user(user_id, {
        "points": user["points"] + points,
        "total_earned": user["total_earned"] + points,
        "tasks_done": user["tasks_done"] + 1
    })

def get_all_users() -> dict:
    return _load()

def create_withdraw_request(user_id: int, points: int, bank_info: str) -> str:
    user = get_user(user_id)
    import time
    req_id = f"WD{int(time.time())}"
    
    history = user.get("withdraw_history", [])
    history.append({
        "id": req_id,
        "points": points,
        "bank_info": bank_info,
        "status": "pending",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    update_user(user_id, {
        "points": user["points"] - points,
        "pending_withdraw": user.get("pending_withdraw", 0) + points,
        "withdraw_history": history
    })
    return req_id
