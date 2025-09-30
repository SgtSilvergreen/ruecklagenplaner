# core/calc.py
from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import pandas as pd  # <- wichtig!
from i18n import MONTHS, CYCLES


def _safe_cycle_months(entry: Dict, lang: str) -> int:
    label = (entry.get("cycle") or "").strip()
    # Mapping pro Sprache
    lang_map = CYCLES.get(lang, CYCLES["de"])
    if label in lang_map and lang_map[label] is not None:
        try:
            return int(lang_map[label])
        except Exception:
            pass
    # Benutzerdefiniert / Custom
    if label in lang_map and lang_map[label] is None:
        try:
            cm = int(entry.get("custom_cycle") or 0)
            return cm if cm > 0 else 12
        except Exception:
            return 12
    # Fallback
    return 12


def get_next_due_date(entry: Dict, lang: str) -> Optional[datetime]:
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")

    try:
        due_month = int(entry["due_month"])
    except Exception:
        due_month = contract_start.month

    cycle_months = _safe_cycle_months(entry, lang)
    end = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else None

    first_due = datetime(year=contract_start.year, month=due_month, day=1)
    if first_due < contract_start:
        first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)

    # Wenn Start bereits im Fälligkeitsmonat liegt, erste Abbuchung erst nach einem Zyklus
    if contract_start.year == first_due.year and contract_start.month == first_due.month:
        first_due = first_due + pd.DateOffset(months=cycle_months)

    next_due = first_due
    while next_due < today:
        next_due = next_due + pd.DateOffset(months=cycle_months)
        if end and next_due > end:
            return None

    if end and next_due > end:
        return None
    return next_due


def get_next_due_text(entry: Dict, lang: str) -> str:
    nd = get_next_due_date(entry, lang)
    if not nd:
        return "—"
    # MONTHS[lang] ist 1-indexiert
    return f"{MONTHS[lang][nd.month]} {nd.year}"


def calculate_monthly_saving_and_progress(entry: Dict, lang: str) -> Tuple[float, float, float, Optional[str]]:
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")

    try:
        due_month = int(entry["due_month"])
    except Exception:
        due_month = contract_start.month

    cycle = _safe_cycle_months(entry, lang)
    amount = float(entry.get("amount") or 0.0)

    # Erste Fälligkeit (Monatsanfang)
    first_due = datetime(year=contract_start.year, month=due_month, day=1)
    if first_due < contract_start:
        first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)

    # Vertrag noch nicht gestartet
    if today < contract_start:
        return 0.0, 0.0, 0.0, contract_start.strftime("%m.%Y")

    # Liegt der Start im Fälligkeitsmonat, zählt dieser Monat direkt als Abbuchung
    if contract_start.year == first_due.year and contract_start.month == first_due.month:
        months_total = cycle
        cycle_start = contract_start
        next_due = first_due
    else:
        # erster Teil-Zyklus
        months_total = (first_due.year - contract_start.year) * 12 + (first_due.month - contract_start.month)
        cycle_start = contract_start
        next_due = first_due

    # in den aktuellen Zyklus springen
    while today >= next_due:
        cycle_start = next_due
        next_due = next_due + pd.DateOffset(months=cycle)
        months_total = cycle

    # innerhalb des aktuellen Zyklus: wie viele Monate bereits vergangen?
    months_saved = (today.year - cycle_start.year) * 12 + (today.month - cycle_start.month)
    if today >= cycle_start:
        months_saved += 1
    months_saved = max(0, min(months_saved, months_total))

    rate = amount / months_total if months_total and months_total > 0 else 0.0
    saved = rate * months_saved
    percent = (saved / amount) if amount > 0 else 0.0
    return rate, percent, saved, None


def calculate_saldo_over_time(entries: List[Dict], lang: str, months_before: int = 36, months_after: int = 36) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame(columns=["month", "saldo"])

    earliest_start = min(datetime.strptime(e["start_date"], "%Y-%m") for e in entries)
    today = datetime.now().replace(day=1)
    base_start = min(today, earliest_start)
    start_candidate = base_start - pd.DateOffset(months=months_before)
    start_date = earliest_start if start_candidate < earliest_start else start_candidate
    end_date = today + pd.DateOffset(months=months_after)

    months = pd.date_range(start=start_date, end=end_date, freq="MS")
    saldo: Dict[str, float] = {}
    account = 0.0

    # Vorberechnungen pro Eintrag
    pre = []
    for entry in entries:
        eid = entry.get("id")
        start_dt = datetime.strptime(entry["start_date"], "%Y-%m")
        end_dt = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else months[-1]
        amount = float(entry.get("amount") or 0.0)
        cycle_months = _safe_cycle_months(entry, lang)

        try:
            due_month = int(entry.get("due_month") or start_dt.month)
        except Exception:
            due_month = start_dt.month

        first_due = datetime(year=start_dt.year, month=due_month, day=1)
        if first_due < start_dt:
            first_due = datetime(year=start_dt.year + 1, month=due_month, day=1)

        # Wenn Start gleich Fälligkeit: erste Abbuchung im selben Monat -> nächster Zyklus vorbereiten
        if start_dt.year == first_due.year and start_dt.month == first_due.month:
            first_due = first_due + pd.DateOffset(months=cycle_months)
            months_left = cycle_months
        else:
            months_left = (first_due.year - start_dt.year) * 12 + (first_due.month - start_dt.month)

        initial_rate = amount / months_left if months_left and months_left > 0 else amount
        pre.append({
            "id": eid,
            "start": start_dt,
            "end": end_dt,
            "amount": amount,
            "cycle_months": cycle_months,
            "next_due": first_due,
            "rate": initial_rate,
            "first_cycle": True,
        })

    # Monat für Monat simulieren
    for month in months:
        key = month.strftime("%Y-%m")
        monthly_plus = 0.0
        monthly_minus = 0.0

        for pe in pre:
            if month < pe["start"] or month > pe["end"]:
                continue

            next_due = pe["next_due"]
            rate = pe["rate"]

            if pe["first_cycle"]:
                if month < next_due:
                    monthly_plus += rate
                elif (month.year, month.month) == (next_due.year, next_due.month):
                    monthly_minus += pe["amount"]
                    pe["next_due"] = next_due + pd.DateOffset(months=pe["cycle_months"])
                    pe["rate"] = pe["amount"] / pe["cycle_months"] if pe["cycle_months"] > 0 else pe["amount"]
                    pe["first_cycle"] = False
                    monthly_plus += pe["rate"]
            else:
                if (month.year, month.month) == (next_due.year, next_due.month):
                    monthly_minus += pe["amount"]
                    pe["next_due"] = next_due + pd.DateOffset(months=pe["cycle_months"])
                    pe["rate"] = pe["amount"] / pe["cycle_months"] if pe["cycle_months"] > 0 else pe["amount"]
                    monthly_plus += pe["rate"]
                elif month > pe["start"] and month < next_due:
                    monthly_plus += rate

        account += monthly_plus
        account -= monthly_minus
        saldo[key] = account

    df_saldo = pd.DataFrame([{"month": k, "saldo": v} for k, v in saldo.items()])
    return df_saldo