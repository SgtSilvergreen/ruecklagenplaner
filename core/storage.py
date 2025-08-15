import json, base64, os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any
from .config import BASE_DIR
from .crypto import encrypt_bytes, decrypt_bytes

def _user_dir(username: str) -> Path:
    """Return/Create absolute data directory for a given user."""
    p = BASE_DIR / "data" / "users" / username
    p.mkdir(parents=True, exist_ok=True)
    return p

def user_entries_path(username: str) -> Path:
    return _user_dir(username) / "entries.json"

def user_notifications_path(username: str) -> Path:
    return _user_dir(username) / "notifications.json"

# --------- intern: enc-wrapper ---------
ENC_MARK = "__rp_enc__"
ENC_KIND = "fernet"

def _load_json_or_enc(p: Path, fkey: Optional[bytes]) -> Tuple[Optional[Any], bool]:
    """Load JSON file that may be plaintext or encrypted.
    Returns (payload, was_encrypted).
    """
    if not p.exists():
        return None, False  # (payload, encrypted?)
    raw = p.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict) and data.get(ENC_MARK) == ENC_KIND:
            if not fkey:
                raise ValueError("Encrypted data present but no key provided")
            ct = base64.b64decode(data["ct"])
            dec = decrypt_bytes(ct, fkey)
            payload = json.loads(dec.decode("utf-8"))
            return payload, True
        # plaintext payload
        return data, False
    except Exception:
         # Not JSON? treat as ciphertext blob
         if not fkey:
             raise
         dec = decrypt_bytes(raw, fkey)
         payload = json.loads(dec.decode("utf-8"))
         return payload, True

def _dump_json_enc(payload: Any, fkey: Optional[bytes]) -> bytes:
    """Dump payload to bytes, optionally encrypted with Fernet."""
    if not fkey:
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    ct = encrypt_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), fkey)
    wrapper = {ENC_MARK: ENC_KIND, "ct": base64.b64encode(ct).decode("ascii")}
    return json.dumps(wrapper, ensure_ascii=False, indent=2).encode("utf-8")

# --------- öffentliche API ---------
def load_entries(username: str, fkey: Optional[bytes] = None) -> List[Dict]:
    p = user_entries_path(username)
    payload, _enc = _load_json_or_enc(p, fkey)
    if payload is None: return []
    return payload if isinstance(payload, list) else []

def save_entries(username: str, entries: List[Dict], fkey: Optional[bytes] = None) -> None:
    p = user_entries_path(username)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_bytes(_dump_json_enc(entries, fkey))
    tmp.replace(p)

def load_notifications(username: str, fkey: Optional[bytes] = None) -> List[Dict]:
    p = user_notifications_path(username)
    payload, _enc = _load_json_or_enc(p, fkey)
    if payload is None: return []
    return payload if isinstance(payload, list) else []

def save_notifications(username: str, notes: List[Dict], fkey: Optional[bytes] = None) -> None:
    p = user_notifications_path(username)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_bytes(_dump_json_enc(notes, fkey))
    tmp.replace(p)

def backup_entries(username: str, reason: str, fkey: Optional[bytes] = None) -> None:
    try:
        bdir = _user_dir(username) / "backups"
        bdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        # sichern IMMER verschlüsselt, wenn Key vorhanden
        src = user_entries_path(username)
        if src.exists():
            payload, _ = _load_json_or_enc(src, fkey)
            data = _dump_json_enc(payload or [], fkey)
            (bdir / f"entries_{ts}_{reason}.json").write_bytes(data)
    except Exception as ex:
        # best-effort: don't crash the app on backup failure
        #         # (could plug in a logger here)
        _ = ex

def wipe_user(username: str) -> None:
    save_entries(username, [], None)
    save_notifications(username, [], None)
    bdir = _user_dir(username) / "backups"
    if bdir.exists():
        for fn in bdir.iterdir():
            try: fn.unlink()
            except Exception: pass

def rewrap_user_data(username: str, old_fkey: Optional[bytes], new_fkey: bytes) -> None:
    try:
        # entries
        entries = load_entries(username, old_fkey)
        save_entries(username, entries, new_fkey)
        # notifications
        notes = load_notifications(username, old_fkey)
        save_notifications(username, notes, new_fkey)
        # backups rewrap (best effort)
        bdir = _user_dir(username) / "backups"
        if bdir.exists():
            for fp in bdir.glob("*.json"):
                try:
                    payload, _ = _load_json_or_enc(fp, old_fkey)
                    if payload is None: payload = []
                    fp.write_bytes(_dump_json_enc(payload, new_fkey))
                except Exception:
                    continue
    except Exception as ex:
        _ = ex

def entries_export(username: str, fkey: bytes | None = None) -> list[dict]:
    return load_entries(username, fkey)

def entries_import(username: str, data: Any, replace: bool, fkey: bytes | None = None) -> bool:
    try:
        # 1) Eingabe ggf. entschlüsseln
        if isinstance(data, dict) and data.get(ENC_MARK) == ENC_KIND:
            if not fkey:
                raise ValueError("Encrypted import requires an active session (key).")
            from .crypto import decrypt_bytes
            ct = base64.b64decode(data["ct"])
            dec = decrypt_bytes(ct, fkey).decode("utf-8")
            data = json.loads(dec)

        # 2) Validierung
        if not isinstance(data, list):
            raise ValueError("Invalid import format: expected a list of entries")

        # ids sicherstellen
        import uuid as _uuid
        for e in data:
            if not isinstance(e, dict):
                raise ValueError("Invalid entry in import list")
            if not e.get("id"):
                e["id"] = str(_uuid.uuid4())

        # 3) Replace/Merge + Backup
        if replace:
            backup_entries(username, "import_replace", fkey)
            save_entries(username, data, fkey)
        else:
            current = load_entries(username, fkey)
            have = {e.get("id") for e in current}
            merged = current + [e for e in data if e.get("id") not in have]
            backup_entries(username, "import_merge", fkey)
            save_entries(username, merged, fkey)

        return True
    except Exception:
        return False
    
def get_categories(username: str, fkey: Optional[bytes] = None, include_empty: bool = False) -> list[str]:
    entries = load_entries(username, fkey)
    vals: Set[str] = set()
    for e in entries:
        v = (e or {}).get("category", "")
        if v is None:
            continue
        v = str(v).strip()
        if v or include_empty:
            vals.add(v)
    return sorted(vals, key=str.casefold)

def get_accounts(username: str, fkey: Optional[bytes] = None, include_empty: bool = False) -> list[str]:
    entries = load_entries(username, fkey)
    vals: Set[str] = set()
    for e in entries:
        v = (e or {}).get("konto", "")
        if v is None:
            continue
        v = str(v).strip()
        if v or include_empty:
            vals.add(v)
    return sorted(vals, key=str.casefold)

def _is_writable(p: Path) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        test = p / ".write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
        return True
    except Exception:
        return False

def ensure_streamlit_config(default_theme: str = "light") -> Path:
    """
    Ensure .streamlit/config.toml exists for this instance.
    - Prefers project-local .streamlit if writable.
    - Falls back to user home (~/.streamlit) if project dir is read-only.
    - Does NOT overwrite an existing config.
    Returns the path to config.toml.
    """
    # 1) preferred: project-local
    local_dir = BASE_DIR / ".streamlit"
    # 2) fallback: user home
    home_dir = Path(os.path.expanduser("~")) / ".streamlit"

    target_dir = local_dir if _is_writable(local_dir) else home_dir
    cfg = target_dir / "config.toml"

    if not cfg.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        cfg.write_text(
            f"""# Auto-generated on first run
[theme]
base = "{default_theme}"

[server]
# keep defaults minimal; customize via deployment (systemd/nginx)
headless = true
enableCORS = false

[browser]
gatherUsageStats = false
""",
            encoding="utf-8",
        )
    return cfg