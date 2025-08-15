from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
from i18n import MONTHS
from .calc import get_next_due_text
from .cycles import safe_cycle_months, months_to_next_occurrence

def _monthly_rate(entry: Dict, lang: str) -> float:
    amt = float(entry.get("amount", 0) or 0)
    cm = safe_cycle_months(entry, lang, "Benutzerdefiniert" if lang=="de" else "Custom")
    return amt / cm if cm > 0 else 0.0

def notify_on_add(append_fn, entry: Dict, currency: str, lang: str, t):
    try:
        txt = t("notif_new_entry").format(
            name=entry.get("name", ""),
            rate=f"{_monthly_rate(entry, lang):.2f} {currency}",
            amount=f"{float(entry.get('amount',0)):.2f} {currency}",
            due=get_next_due_text(entry, lang),
        )
        append_fn([{
            "entry_id": entry.get("id"),
            "type": "new_entry",
            "effective_month": datetime.now().strftime("%Y-%m"),
            "text": txt,
            "read": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
    except Exception:
        pass

def notify_on_update(append_fn, old: Dict, new: Dict, currency: str, lang: str, t, prefs: Dict):
    try:
        notes = []
        r_old, r_new = _monthly_rate(old, lang), _monthly_rate(new, lang)
        if prefs.get("notif_event_rate", True) and abs(r_old - r_new) > 1e-6:
            notes.append({
                "entry_id": new.get("id"),
                "type": "rate_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_rate_changed").format(
                    name=new.get("name",""),
                    old=f"{r_old:.2f} {currency}",
                    new=f"{r_new:.2f} {currency}",
                ),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        nd_old, nd_new = get_next_due_text(old, lang), get_next_due_text(new, lang)
        if prefs.get("notif_event_due", True) and nd_old != nd_new:
            notes.append({
                "entry_id": new.get("id"),
                "type": "due_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_due_changed").format(name=new.get("name",""), old=nd_old, new=nd_new),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        amt_old, amt_new = float(old.get("amount",0) or 0), float(new.get("amount",0) or 0)
        if prefs.get("notif_event_amount", True) and abs(amt_old - amt_new) > 1e-6:
            notes.append({
                "entry_id": new.get("id"),
                "type": "amount_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_amount_changed").format(
                    name=new.get("name",""),
                    old=f"{amt_old:.2f} {currency}",
                    new=f"{amt_new:.2f} {currency}",
                ),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        # cycle text wird im UI gerendert, hier genügt Typ
        if prefs.get("notif_event_cycle", True) and (old.get("cycle"), old.get("custom_cycle")) != (new.get("cycle"), new.get("custom_cycle")):
            notes.append({
                "entry_id": new.get("id"),
                "type": "cycle_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_cycle_changed").format(name=new.get("name",""), old="-", new="-"),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        append_fn(notes)
    except Exception:
        pass

def notify_on_delete(append_fn, entry: Dict, t):
    try:
        append_fn([{
            "entry_id": entry.get("id"),
            "type": "entry_deleted",
            "effective_month": datetime.now().strftime("%Y-%m"),
            "text": t("notif_deleted").format(name=entry.get("name","")),
            "read": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
    except Exception:
        pass

def ensure_monthly_notifications(load_entries_fn, load_notes_fn, save_notes_fn, lang: str, currency: str, t):
    prefs = {}  # prefs check erfolgt im Aufrufer; hier einfache Variante
    notes = load_notes_fn()
    existing = {(n.get("entry_id"), n.get("effective_month"), n.get("type")) for n in notes}
    now = datetime.now().replace(day=1)
    ym = now.strftime("%Y-%m")
    new = []
    for e in load_entries_fn():
        from .calc import get_next_due_date
        nd = get_next_due_date(e, lang)
        if nd and nd.year == now.year and nd.month == now.month:
            key = (e["id"], ym, "due")
            if key not in existing:
                txt = t("notif_due_this_month").format(
                    name=e.get("name",""),
                    amount=f"{float(e.get('amount',0)):.2f} {currency}",
                    due=f"{MONTHS[lang][nd.month]} {nd.year}",
                    rate=f"{_monthly_rate(e, lang):.2f} {currency}",
                )
                new.append({
                    "entry_id": e["id"],
                    "type": "due",
                    "effective_month": ym,
                    "text": txt,
                    "read": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    if new:
        save_notes_fn(notes + new)

def evaluate_events(entries: list[dict], rules, lang: str, today: date | None = None) -> list[dict]:
    """Create per-entry notification events based on upcoming dues and end dates."""
    if today is None:
        today = date.today()
    out = []
    for e in entries:
        # Nächste Fälligkeit
        if rules["due_upcoming"].enabled:
            months = months_to_next_occurrence(e, lang)
            # Einfacher Ansatz: wenn innerhalb lead_days
            # (aus months grob in Tage umrechnen):
            days = int(months * 30)  # pragmatisch
            if 0 <= days <= rules["due_upcoming"].lead_days:
                out.append({
                    "type": "due_upcoming",
                    "entry_id": e["id"],
                    "title": t("notif_due_upcoming_title").format(name=e["name"]),
                    "read": False,
                    "ts": today.isoformat(),
                })

        # Enddatum
        if rules["end_upcoming"].enabled and (end := e.get("end_date")):
            try:
                y, m = map(int, end.split("-")[:2])
                # setze Enddatum auf den 1. des Monats
                from datetime import date as _d
                ed = _d(y, m, 1)
                if 0 <= (ed - today).days <= rules["end_upcoming"].end_lead_days:
                    out.append({
                        "type": "end_upcoming",
                        "entry_id": e["id"],
                        "title": t("notif_end_upcoming_title").format(name=e["name"], end=end),
                        "read": False,
                        "ts": today.isoformat(),
                    })
            except Exception:
                pass

    return out
