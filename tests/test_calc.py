from datetime import datetime
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

import core.calc as calc  # noqa: E402
from core.utils import due_month_sort_value  # noqa: E402


class _FixedDateTime(datetime):
    """Helper datetime subclass that freezes now() for deterministic tests."""

    _NOW = datetime(2025, 9, 1)

    @classmethod
    def now(cls):
        return cls._NOW

    @classmethod
    def strptime(cls, *args, **kwargs):
        return datetime.strptime(*args, **kwargs)


def test_progress_complete_month_before_due(monkeypatch):
    monkeypatch.setattr(calc, "datetime", _FixedDateTime)

    entry = {
        "start_date": "2024-10",
        "due_month": "10",
        "cycle": "Jährlich",
        "amount": 900,
    }

    rate, percent, saved, info = calc.calculate_monthly_saving_and_progress(entry, "de")

    assert rate == pytest.approx(75.0)
    assert percent == pytest.approx(1.0)
    assert saved == pytest.approx(entry["amount"])
    assert info is None


def test_progress_stops_after_end(monkeypatch):
    class _EndDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 9, 1)

    monkeypatch.setattr(calc, "datetime", _EndDateTime)

    entry = {
        "start_date": "2024-01",
        "due_month": "03",
        "cycle": "Jährlich",
        "amount": 600,
        "end_date": "2025-03",
    }

    rate, percent, saved, info = calc.calculate_monthly_saving_and_progress(entry, "de")

    assert rate == pytest.approx(0.0)
    assert percent == pytest.approx(0.0)
    assert saved == pytest.approx(0.0)
    assert info is None


def test_due_month_sort_value_wraps_year():
    entries = [
        {"name": "A", "due_month": 11},
        {"name": "B", "due_month": 10},
        {"name": "C", "due_month": 3},
    ]

    reference = datetime(2025, 10, 1)
    ordered = sorted(entries, key=lambda e: due_month_sort_value(e, reference, "de"))

    assert [e["name"] for e in ordered] == ["B", "A", "C"]


def test_due_month_sort_uses_next_due_date(monkeypatch):
    class _FakeDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 9, 15)

    monkeypatch.setattr("core.calc.datetime", _FakeDateTime)

    entry_current_year = {
        "name": "Aktuell",
        "due_month": 11,
        "start_date": "2024-01",
        "cycle": "Jährlich",
        "amount": 100,
    }
    entry_next_year = {
        "name": "Später",
        "due_month": 11,
        "start_date": "2025-12",
        "cycle": "Jährlich",
        "amount": 100,
    }

    reference = datetime(2025, 10, 1)
    ordered = sorted(
        [entry_next_year, entry_current_year],
        key=lambda e: due_month_sort_value(e, reference, "de"),
    )

    assert [e["name"] for e in ordered] == ["Aktuell", "Später"]


def test_saved_totals_match_history(monkeypatch):
    class _HistoryDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 9, 1)

    monkeypatch.setattr(calc, "datetime", _HistoryDateTime)

    entries = [
        {
            "id": 1,
            "name": "Aktiv",
            "start_date": "2024-01",
            "due_month": "10",
            "cycle": "Jährlich",
            "amount": 1200,
        },
        {
            "id": 2,
            "name": "Beendet",
            "start_date": "2024-01",
            "due_month": "03",
            "cycle": "Jährlich",
            "amount": 600,
            "end_date": "2025-03",
        },
    ]

    total_saved = 0.0
    for entry in entries:
        _, _, saved, _ = calc.calculate_monthly_saving_and_progress(entry, "de")
        total_saved += saved

    df = calc.calculate_saldo_over_time(entries, "de", months_before=0, months_after=0)
    saldo_today = df[df["month"] == "2025-09"]["saldo"].iloc[0]

    assert total_saved == pytest.approx(saldo_today)


def test_saldo_drops_closed_entry_balance(monkeypatch):
    class _HistoryDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 9, 1)

    monkeypatch.setattr(calc, "datetime", _HistoryDateTime)

    entries = [
        {
            "id": 1,
            "name": "Ende vor Fälligkeit",
            "start_date": "2025-01",
            "due_month": "07",
            "cycle": "Jährlich",
            "amount": 1200,
            "end_date": "2025-05",
        }
    ]

    total_saved = sum(
        calc.calculate_monthly_saving_and_progress(entry, "de")[2]
        for entry in entries
    )

    df = calc.calculate_saldo_over_time(entries, "de", months_before=0, months_after=0)
    saldo_today = df[df["month"] == "2025-09"]["saldo"].iloc[0]

    assert total_saved == pytest.approx(0.0)
    assert saldo_today == pytest.approx(total_saved)
