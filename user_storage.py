import json
from pathlib import Path
from typing import List
from models import User

USERS_FILE = Path("users.json")

def _ensure_users_file():
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]")

def load_users() -> List[User]:
    _ensure_users_file()
    data = json.loads(USERS_FILE.read_text())
    return [User(**u) for u in data]

def save_users(users: List[User]) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump([u.dict() for u in users], f, indent=4)
