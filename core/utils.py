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


def due_month_sort_value(entry: Dict, reference_month: int | None = None) -> Tuple[int, int, str]:
    """Return a tuple that can be used to sort entries by due month.

    The tuple rotates months so that sorting starts with the month nearest to the
    provided reference month (default: the current month).
    """

    ref = reference_month or datetime.now().month
    due_month = _normalize_due_month(entry)
    rotation = (due_month - ref) % 12
    name = (entry.get("name") or "").lower()
    return rotation, due_month, name
