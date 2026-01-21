import json
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent
RES_PATH = BASE_PATH / "resources"
MSG_PATH = RES_PATH / "messages"
IMG_PATH = RES_PATH / "images"

def get_text(name: str, folder: str = "") -> str:
    path = MSG_PATH / folder / f"{name}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else f"Текст {name} не знайдено."

def get_image(name: str, folder: str = "") -> Path:
    return IMG_PATH / folder / f"{name}.png"

def get_player_path(user_id: int) -> Path:
    return BASE_PATH / "players" / f"{user_id}.json"

def load_player(user_id: int) -> dict:
    path = get_player_path(user_id)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_player(user_id: int, data: dict):
    path = get_player_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_player(user_id: int, stat_change: dict = None, item: str = None):
    data = load_player(user_id)
    if not data:
        return
        
    if stat_change:
        for stat, val in stat_change.items():
            data["stats"][stat] = data["stats"].get(stat, 0) + val
            
    if item:
        inventory = data.setdefault("inventory", [])
        if item not in inventory:
            inventory.append(item)
            
    save_player(user_id, data)
