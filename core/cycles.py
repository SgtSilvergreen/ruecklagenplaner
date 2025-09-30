from datetime import datetime
from typing import Any, Dict, Optional

from i18n import CYCLES, TURNUS_LABELS_EN

from .calc import get_next_due_date

def get_turnus_mapping(lang: str) -> Dict[str, Optional[int]]:
    return CYCLES.get(lang, CYCLES["de"]).copy()

def safe_cycle_months(entry: Dict[str, Any], lang: str, custom_label: str) -> int:
    cycle = str(entry.get("cycle") or "")
    if cycle == custom_label:
        cm_raw = entry.get("custom_cycle")
    else:
        cm_raw = get_turnus_mapping(lang).get(cycle)
    try:
        cm = int(cm_raw) if cm_raw is not None else 0
    except (TypeError, ValueError):
        cm = 0
    return cm if cm > 0 else 12

def turnus_label(entry: Dict[str, Any], lang: str, custom_label: str) -> str:
    cycle = str(entry.get("cycle") or "")
    if cycle == custom_label:
        n = int(entry.get("custom_cycle") or 0)
        return (f"{custom_label} ({n} Mon.)" if lang=="de" else f"{custom_label} ({n} mo)") if n else custom_label
    months = get_turnus_mapping(lang).get(cycle)
    if lang == "de":
        return f"{cycle} ({months} Mon.)" if months else cycle or "-"
    display = TURNUS_LABELS_EN.get(cycle, cycle or "-")
    return f"{display} ({months} mo)" if months else display

def months_to_next_occurrence(entry: Dict[str, Any], lang: str) -> Optional[int]:
    next_due = get_next_due_date(entry, lang)
    if not next_due:
        return None
    today = datetime.now().replace(day=1)
    diff_months = (next_due.year - today.year) * 12 + (next_due.month - today.month)
    return max(0, diff_months)