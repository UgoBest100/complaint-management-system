import json
from pathlib import Path
from typing import List
from models import Complaint

COMPLAINTS_FILE = Path("complaints.json")

def _ensure_complaints_file():
    if not COMPLAINTS_FILE.exists():
        COMPLAINTS_FILE.write_text("[]")

def load_complaints() -> List[Complaint]:
    _ensure_complaints_file()
    data = json.loads(COMPLAINTS_FILE.read_text())
    return [Complaint(**c) for c in data]

def save_complaints(complaints: List[Complaint]) -> None:
    with open(COMPLAINTS_FILE, "w") as f:
        from datetime import datetime

        json.dump(
            [c.dict() for c in complaints],
            f,
            indent=4,
            default=str  # This will convert datetime to string
        )

