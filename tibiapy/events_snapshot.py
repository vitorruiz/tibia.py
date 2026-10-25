"""Static snapshot of the event calendar consumed by the Tibia Companion app.

The app reads a single JSON file with the schedules of the previous, current and next month, in the same shape the
``/events/{year}/{month}`` endpoint returns for each of them.
"""
from __future__ import annotations

import datetime
from typing import Any

from tibiapy.models import EventSchedule

__all__ = (
    "build_events_snapshot",
    "months_around",
    "schedule_to_dict",
)


def months_around(today: datetime.date) -> list[tuple[int, int]]:
    """Get the ``(year, month)`` pairs of the previous, current and next month."""
    previous = (today.replace(day=1) - datetime.timedelta(days=1))
    following = (today.replace(day=28) + datetime.timedelta(days=4))
    return [(m.year, m.month) for m in (previous, today, following)]


def schedule_to_dict(schedule: EventSchedule) -> dict[str, Any]:
    """Convert a month's schedule into the JSON structure the app expects."""
    return {
        "year": schedule.year,
        "month": schedule.month,
        "events": [
            {
                "title": event.title,
                "description": event.description,
                "startDate": event.start_date.isoformat() if event.start_date else None,
                "endDate": event.end_date.isoformat() if event.end_date else None,
                "duration": event.duration,
                "color": event.color,
            }
            for event in schedule.events
        ],
    }


def build_events_snapshot(schedules: list[EventSchedule], now: datetime.datetime) -> dict[str, Any]:
    """Build the snapshot with every schedule that was fetched."""
    return {
        "generatedAt": now.isoformat(),
        "schedules": [schedule_to_dict(s) for s in schedules],
    }
