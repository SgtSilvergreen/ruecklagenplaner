# core/config.py
import json
from pathlib import Path
from typing import Dict

# Projekt-Root (Ordner, in dem Ruecklagenplaner.py liegt)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
USERS_FILE = DATA_DIR / "users.json"
VERSION_FILE = BASE_DIR / "VERSION"

def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_settings() -> Dict:
    ensure_dirs()
    default = {"language": "de", "currency": "€"}
    if not SETTINGS_FILE.exists():
        return default
    try:
        return {**default, **json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))}
    except Exception:
        return default

def save_settings(settings: Dict):
    ensure_dirs()
    tmp = SETTINGS_FILE.with_suffix(SETTINGS_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SETTINGS_FILE)

def get_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "0.0.0"