from i18n import CYCLES, TURNUS_LABELS_EN
from datetime import datetime
from typing import Optional
from .calc import get_next_due_date

def get_turnus_mapping(lang: str) -> dict:
    return CYCLES.get(lang, CYCLES["de"]).copy()

def safe_cycle_months(entry: dict, lang: str, custom_label: str) -> int:
    if entry.get("cycle") == custom_label:
        cm = entry.get("custom_cycle")
    else:
        cm = get_turnus_mapping(lang).get(entry.get("cycle"))
    try:
        cm = int(cm)
    except Exception:
        cm = 0
    return cm if cm and cm > 0 else 12

def turnus_label(entry: dict, lang: str, custom_label: str) -> str:
    if entry.get("cycle") == custom_label:
        n = int(entry.get("custom_cycle") or 0)
        return (f"{custom_label} ({n} Mon.)" if lang=="de" else f"{custom_label} ({n} mo)") if n else custom_label
    months = get_turnus_mapping(lang).get(entry.get("cycle"))
    if lang == "de":
        return f"{entry.get('cycle')} ({months} Mon.)" if months else entry.get('cycle', '-')
    display = TURNUS_LABELS_EN.get(entry.get('cycle'), entry.get('cycle', '-'))
    return f"{display} ({months} mo)" if months else display

def months_to_next_occurrence(entry: dict, lang: str) -> Optional[int]:
    next_due = get_next_due_date(entry, lang)
    if not next_due:
        return None
    today = datetime.now().replace(day=1)
    diff_months = (next_due.year - today.year) * 12 + (next_due.month - today.month)
    return max(0, diff_months)