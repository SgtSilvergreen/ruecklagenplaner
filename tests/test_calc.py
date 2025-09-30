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


def test_due_month_sort_value_wraps_year():
    entries = [
        {"name": "A", "due_month": 11},
        {"name": "B", "due_month": 10},
        {"name": "C", "due_month": 3},
    ]

    ordered = sorted(entries, key=lambda e: due_month_sort_value(e, reference_month=9))

    assert [e["name"] for e in ordered] == ["B", "A", "C"]
