# core/calc.py
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd  # <- wichtig!
from i18n import MONTHS, CYCLES


def _month_add(base: datetime, months: int) -> datetime:
    """Return the first day of the month that lies ``months`` after ``base``."""

    year = base.year + (base.month - 1 + months) // 12
    month = ((base.month - 1 + months) % 12) + 1
    return datetime(year, month, 1)


def _safe_cycle_months(entry: Dict[str, Any], lang: str) -> int:
    label = str(entry.get("cycle") or "").strip()
    lang_map: Dict[str, Optional[int]] = CYCLES.get(lang, CYCLES["de"])
    value = lang_map.get(label)
    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    if value is None and label in lang_map:
        try:
            cm = int(entry.get("custom_cycle") or 0)
            return cm if cm > 0 else 12
        except (TypeError, ValueError):
            return 12
    return 12


def get_next_due_date(entry: Dict[str, Any], lang: str) -> Optional[datetime]:
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")

    try:
        due_month = int(entry["due_month"])
    except Exception:
        due_month = contract_start.month

    cycle_months = int(_safe_cycle_months(entry, lang))
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


def calculate_monthly_saving_and_progress(entry: Dict[str, Any], lang: str) -> Tuple[float, float, float, Optional[str]]:
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")
    contract_end = None
    if entry.get("end_date"):
        contract_end = datetime.strptime(entry["end_date"], "%Y-%m")

    try:
        due_month = int(entry["due_month"])
    except Exception:
        due_month = contract_start.month

    cycle_months = int(_safe_cycle_months(entry, lang))
    amount = float(entry.get("amount") or 0.0)

    # Noch nicht gestartet
    if today < contract_start:
        return 0.0, 0.0, 0.0, contract_start.strftime("%m.%Y")

    # Ersten Fälligkeitstermin bestimmen
    first_due = datetime(year=contract_start.year, month=due_month, day=1)
    if first_due < contract_start:
        first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)

    months_first_cycle = (first_due.year - contract_start.year) * 12 + (
        first_due.month - contract_start.month
    )
    if contract_start.year == first_due.year and contract_start.month == first_due.month:
        months_first_cycle = cycle_months
        first_due = _month_add(first_due, cycle_months)

    # Simulation bis zum relevanten Monat (Ende berücksichtigen)
    effective_today = today
    if contract_end and effective_today > contract_end:
        effective_today = contract_end

    account = 0.0
    current_rate = 0.0

    next_due = first_due
    cycle_start = contract_start
    first_cycle = True

    month = contract_start
    while month <= effective_today:
        if contract_end and month > contract_end:
            break

        if first_cycle:
            if month < next_due:
                account += amount / months_first_cycle if months_first_cycle > 0 else 0.0
                current_rate = amount / months_first_cycle if months_first_cycle > 0 else 0.0
            elif month == next_due:
                account -= amount
                next_due = _month_add(next_due, cycle_months)
                first_cycle = False
                cycle_start = month
                if not contract_end or month < contract_end:
                    rate = amount / cycle_months if cycle_months > 0 else amount
                    account += rate
                    current_rate = rate
                else:
                    current_rate = 0.0
        else:
            if month == next_due:
                account -= amount
                cycle_start = month
                next_due = _month_add(next_due, cycle_months)
                if not contract_end or month < contract_end:
                    rate = amount / cycle_months if cycle_months > 0 else amount
                    account += rate
                    current_rate = rate
                else:
                    current_rate = 0.0
            elif month > cycle_start and month < next_due:
                account += current_rate

        month = _month_add(month, 1)

    saved = max(0.0, account)
    percent = (saved / amount) if amount > 0 else 0.0

    if contract_end and today > contract_end:
        # Vertrag ist beendet – abgelaufene Einträge zeigen keine Rate mehr an
        return 0.0, 0.0, 0.0, None

    rate = current_rate
    return rate, min(1.0, percent), saved, None


def calculate_saldo_over_time(entries: List[Dict[str, Any]], lang: str, months_before: int = 36, months_after: int = 36) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame({"month": [], "saldo": []})

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
        end_dt = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else None
        sim_end = end_dt or months[-1]
        amount = float(entry.get("amount") or 0.0)
        cycle_months = int(_safe_cycle_months(entry, lang))

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
            "sim_end": sim_end,
            "amount": amount,
            "cycle_months": cycle_months,
            "next_due": first_due,
            "rate": initial_rate,
            "first_cycle": True,
            "balance": 0.0,
            "closed": False,
        })

    # Monat für Monat simulieren
    for month in months:
        key = month.strftime("%Y-%m")
        monthly_plus = 0.0
        monthly_minus = 0.0

        for pe in pre:
            if pe["end"] and month > pe["end"]:
                if not pe["closed"] and pe["balance"]:
                    monthly_minus += pe["balance"]
                    pe["balance"] = 0.0
                pe["closed"] = True
                continue

            if month < pe["start"] or month > pe["sim_end"]:
                continue

            next_due = pe["next_due"]
            rate = pe["rate"]

            if pe["first_cycle"]:
                if month < next_due:
                    monthly_plus += rate
                    pe["balance"] += rate
                elif (month.year, month.month) == (next_due.year, next_due.month):
                    monthly_minus += pe["amount"]
                    pe["balance"] -= pe["amount"]
                    pe["next_due"] = next_due + pd.DateOffset(months=pe["cycle_months"])
                    pe["rate"] = pe["amount"] / pe["cycle_months"] if pe["cycle_months"] > 0 else pe["amount"]
                    pe["first_cycle"] = False
                    if not pe["end"] or month < pe["end"]:
                        monthly_plus += pe["rate"]
                        pe["balance"] += pe["rate"]
                    else:
                        pe["rate"] = 0.0
            else:
                if (month.year, month.month) == (next_due.year, next_due.month):
                    monthly_minus += pe["amount"]
                    pe["balance"] -= pe["amount"]
                    pe["next_due"] = next_due + pd.DateOffset(months=pe["cycle_months"])
                    if not pe["end"] or month < pe["end"]:
                        pe["rate"] = pe["amount"] / pe["cycle_months"] if pe["cycle_months"] > 0 else pe["amount"]
                        monthly_plus += pe["rate"]
                        pe["balance"] += pe["rate"]
                    else:
                        pe["rate"] = 0.0
                elif month > pe["start"] and month < next_due:
                    monthly_plus += rate
                    pe["balance"] += rate

        account += monthly_plus
        account -= monthly_minus
        saldo[key] = account

    df_saldo = pd.DataFrame([{"month": k, "saldo": v} for k, v in saldo.items()])
    return df_saldo
