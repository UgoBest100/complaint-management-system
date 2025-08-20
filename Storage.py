import json
from typing import List
from models import Complaint
from pathlib import Path

FILE_PATH = "complaints.json"


#function to load complaints
def load_complaints() -> List[Complaint]:
    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            return [Complaint(**item) for item in data]
    except FileNotFoundError:
        return []

#function to save complaints
def save_complaints(complaints: List[Complaint]) ->None:
    with open(FILE_PATH, "w") as f:
        json.dump([c.dict() for c in complaints], f, indent=4)















