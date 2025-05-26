import json
import os

USER_PATH = "data/user_data.json"
FOODS_PATH = "data/food_data.json"

def load():
    if os.path.exists(USER_PATH):
        with open(USER_PATH, "r") as f:
            return json.load(f)
    return {}

def save():
    with open(USER_PATH, "w") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)


def load_foods():
    if os.path.exists(FOODS_PATH):
        with open(FOODS_PATH, "r") as f:
            return json.load(f)
    return {}

def save_foods():
    with open(FOODS_PATH, "w") as f:
        json.dump(food_data, f, ensure_ascii=False, indent=4)


user_data = load()
food_data = load_foods()
