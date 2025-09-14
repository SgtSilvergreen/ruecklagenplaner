from datetime import date
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.notify import evaluate_events
from core.notify_rules import DEFAULT_RULES
from i18n import get_text


def test_evaluate_events_skips_when_no_next_due():
    entries = [{"id": "1", "name": "Test"}]
    with patch("core.notify.months_to_next_occurrence", return_value=None):
        events = evaluate_events(entries, DEFAULT_RULES, "de", today=date(2024, 1, 1))
    assert events == []


def test_evaluate_events_generates_translated_title():
    entries = [{"id": "2", "name": "Foo"}]
    with patch("core.notify.months_to_next_occurrence", return_value=0):
        events = evaluate_events(entries, DEFAULT_RULES, "de", today=date(2024, 1, 1))
    assert events[0]["title"] == get_text("de", "notif_due_upcoming_title").format(name="Foo")

