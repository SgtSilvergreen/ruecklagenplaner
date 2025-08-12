from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from .auth import add_user, find_user, get_user_enc_params, set_user_password
from .crypto import derive_fernet_key
from .storage import save_entries

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo"

def ensure_demo_user(password: str = DEMO_PASSWORD) -> None:
    u = find_user(DEMO_USERNAME)
    if not u:
        add_user(DEMO_USERNAME, password, role="user")

def _mk(name, amount, konto, cat, cycle, due_month, start, end=None, custom_cycle=None):
    return {
        "id": str(uuid.uuid4()),
        "name": name, "amount": float(amount), "konto": konto, "category": cat,
        "cycle": cycle, "custom_cycle": custom_cycle,
        "due_month": int(due_month), "start_date": start, "end_date": end,
    }

def demo_entries() -> list[dict]:
    y = datetime.now().year
    return [
        _mk("Kfz-Versicherung", 600, "Giro", "Versicherungen", "Jährlich", 12, f"{y}-01"),
        _mk("Hausrat",          240, "Giro", "Versicherungen", "Jährlich",  6, f"{y}-02"),
        _mk("Wartung Heizung",  300, "Nebenkosten", "Wartung", "Vierteljährlich", 3, f"{y}-01"),
        _mk("Urlaub",          1800, "Tagesgeld", "Urlaub", "Benutzerdefiniert", 8, f"{y}-01", end=f"{y+1}-08", custom_cycle=18),
        _mk("Rücklage Geräte",  900, "Tagesgeld", "Haushalt", "Halbjährlich", 1, f"{y}-01"),
    ]

def login_as_demo_and_seed() -> tuple[str, bytes | None]:
    """Sorgt für Demo-User + Demo-Daten (verschlüsselt) und gibt (username, fkey) zurück."""
    ensure_demo_user(DEMO_PASSWORD)
    params = get_user_enc_params(DEMO_USERNAME)
    fkey = derive_fernet_key(DEMO_PASSWORD, params["salt"], params["iters"]) if params else None
    # überschreibt bewusst die Demo-Einträge (Demo-Usecase)
    save_entries(DEMO_USERNAME, demo_entries(), fkey)
    return DEMO_USERNAME, fkey