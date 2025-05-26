import json
import os

FILE_PATH = "data/user_data.json"

def load():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            return json.load(f)
    return {}

def save():
    with open(FILE_PATH, "w") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

user_data = load()
