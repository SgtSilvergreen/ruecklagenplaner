from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Rule:
    id: str               # z.B. "due_upcoming"
    enabled: bool
    lead_days: int = 14   # Vorlauf für Fälligkeiten
    end_lead_days: int = 30  # Vorlauf für Enddatum

DEFAULT_RULES = {
    "due_upcoming": Rule("due_upcoming", True, lead_days=14),
    "end_upcoming": Rule("end_upcoming", True, end_lead_days=30),
}