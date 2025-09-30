from __future__ import annotations

from datetime import datetime
from typing import Dict, Tuple


def _normalize_due_month(entry: Dict) -> int:
    """Return the due month for an entry as an integer between 1 and 12."""
    try:
        month = int(entry.get("due_month") or 0)
    except (TypeError, ValueError):
        month = 0
    if 1 <= month <= 12:
        return month
    start = entry.get("start_date") or ""
    try:
        return int(start.split("-")[1])
    except (IndexError, ValueError):
        return datetime.now().month


def next_month_start(from_date: datetime | None = None) -> datetime:
    base = (from_date or datetime.now()).replace(day=1)
    year = base.year + (1 if base.month == 12 else 0)
    month = 1 if base.month == 12 else base.month + 1
    return datetime(year, month, 1)


def due_month_sort_value(
    entry: Dict,
    reference: datetime | None = None,
    lang: str = "de",
) -> Tuple[float, int, str, str]:
    """Return a tuple that can be used to sort entries by their upcoming due date."""

    from core.calc import get_next_due_date

    ref = reference or next_month_start()
    ref = ref.replace(day=1)

    try:
        next_due = get_next_due_date(entry, lang)
    except (KeyError, ValueError):
        next_due = None
    if next_due:
        due_date = next_due.replace(day=1)
    else:
        due_month = _normalize_due_month(entry)
        due_date = datetime(ref.year, due_month, 1)
        while due_date < ref:
            due_date = datetime(due_date.year + 1, due_date.month, 1)

    months_ahead = (due_date.year - ref.year) * 12 + (due_date.month - ref.month)
    account = (entry.get("konto") or "").lower()
    name = (entry.get("name") or "").lower()

    return float(months_ahead), due_date.month, account, name
