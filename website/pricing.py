"""Indicative pricing used by the quote calculator.

Per-service pricing lives on the Service model (``price_from``, ``addon_factor``,
``is_retainer``); the scope sizes and add-ons below apply across all services.
"""

from datetime import datetime, timedelta


SCOPE_SIZES = [
    {"id": "starter", "label": "Starter", "mult": 1, "weeks": "3–4 weeks"},
    {"id": "standard", "label": "Standard", "mult": 1.6, "weeks": "5–8 weeks"},
    {"id": "complex", "label": "Complex", "mult": 2.5, "weeks": "9–14 weeks"},
]

QUOTE_ADDONS = [
    {"id": "content", "label": "Copy & content", "add": 25, "default": True},
    {"id": "training", "label": "Team training", "add": 18, "default": False},
    {"id": "care", "label": "Monthly care", "add": 12, "default": False},
]

SLOT_TIMES = ["10:00", "15:00"]


def upcoming_slots(now=None, count=4):
    """Labels for the next few weekday call slots, e.g. ``Tue 10:00``."""
    now = now or datetime.now()
    slots = []
    day = now.date() + timedelta(days=1)
    while len(slots) < count:
        if day.weekday() < 5:
            for time in SLOT_TIMES:
                if len(slots) < count:
                    slots.append("{} {}".format(day.strftime("%a"), time))
        day += timedelta(days=1)
    return slots
