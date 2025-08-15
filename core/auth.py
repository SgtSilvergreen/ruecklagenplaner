# core/auth.py
import json, base64, hmac, hashlib, secrets
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from .config import USERS_FILE
from .crypto import make_salt, PBKDF2_ITERS_DEFAULT

def _b64(x): return base64.b64encode(x).decode('ascii')
def _b64d(s): return base64.b64decode(s.encode('ascii'))

def make_hash(password: str, iterations: int = PBKDF2_ITERS_DEFAULT) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f"pbkdf2${iterations}${_b64(salt)}${_b64(dk)}"

def verify_password(password: str, stored: str) -> bool:
    try:
        method, iters, salt_b64, hash_b64 = stored.split('$', 3)
        if method != 'pbkdf2': return False
        iters = int(iters)
        salt = _b64d(salt_b64)
        expected = _b64d(hash_b64)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iters)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def _ensure_users_file():
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_users() -> List[Dict]:
    _ensure_users_file()
    if not USERS_FILE.exists(): return []
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_users(users: List[Dict]):
    _ensure_users_file()
    tmp: Path = USERS_FILE.with_suffix(USERS_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(USERS_FILE)

def add_user(username: str, password: str, role: str = "user"):
    users = load_users()
    if any(u.get("username") == username for u in users):
        raise ValueError("User existiert bereits")
    enc_salt = make_salt()
    users.append({
        "username": username,
        "role": role,
        "active": True,
        "pw_hash": make_hash(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": None,
        # neu: Verschlüsselungs-Metadaten pro Nutzer
        "enc": {
            "salt": base64.b64encode(enc_salt).decode("ascii"),
            "iters": PBKDF2_ITERS_DEFAULT,
        },
    })
    save_users(users)

def find_user(username: str) -> Optional[Dict]:
    for u in load_users():
        if u.get("username") == username:
            return u
    return None

def set_user_password(username: str, new_password: str):
    users = load_users()
    for u in users:
        if u.get("username") == username:
            u["pw_hash"] = make_hash(new_password)
            # Salt kann bleiben; alternativ hier neues Salt generieren:
            # u["enc"]["salt"] = base64.b64encode(make_salt()).decode("ascii")
            save_users(users)
            return
    raise ValueError("User nicht gefunden")

def set_user_role(username: str, role: str):
    users = load_users()
    for u in users:
        if u.get("username") == username:
            u["role"] = role
            save_users(users); return
    raise ValueError("User nicht gefunden")

def set_user_active(username: str, active: bool):
    users = load_users()
    for u in users:
        if u.get("username") == username:
            u["active"] = active
            save_users(users); return
    raise ValueError("User nicht gefunden")

def delete_user(requesting_username: str, target_username: str):
    users = load_users()
    if requesting_username == target_username:
        raise ValueError("Du kannst dich nicht selbst löschen")

    target = next((u for u in users if u.get("username") == target_username), None)
    if not target:
        raise ValueError("User nicht gefunden")

    # Wenn Ziel ein Admin ist: bleiben danach noch andere Admins übrig?
    if target.get("role") == "admin":
        remaining_admins = [u for u in users if u.get("role") == "admin" and u.get("username") != target_username]
        if not remaining_admins:
            raise ValueError("Mindestens ein Admin muss verbleiben")

    users = [u for u in users if u.get("username") != target_username]
    save_users(users)

def get_user_enc_params(username: str) -> Optional[dict]:
    u = find_user(username)
    if not u: return None
    enc = u.get("enc") or {}
    try:
        salt = base64.b64decode(enc.get("salt",""))
        iters = int(enc.get("iters") or PBKDF2_ITERS_DEFAULT)
        return {"salt": salt, "iters": iters}
    except Exception:
        return None