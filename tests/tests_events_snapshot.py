import datetime
import json

from tibiapy.events_snapshot import build_events_snapshot, months_around, schedule_to_dict
from tibiapy.models import EventEntry, EventSchedule

from tests.tests_tibiapy import TestCommons


class TestEventsSnapshot(TestCommons):
    def test_months_around_in_the_middle_of_the_year(self):
        self.assertEqual([(2026, 9), (2026, 10), (2026, 11)], months_around(datetime.date(2026, 10, 24)))

    def test_months_around_crosses_year_boundaries(self):
        self.assertEqual([(2025, 12), (2026, 1), (2026, 2)], months_around(datetime.date(2026, 1, 31)))
        self.assertEqual([(2026, 11), (2026, 12), (2027, 1)], months_around(datetime.date(2026, 12, 1)))

    def test_months_around_handles_the_last_day_of_a_month(self):
        self.assertEqual([(2026, 1), (2026, 2), (2026, 3)], months_around(datetime.date(2026, 2, 28)))

    def test_schedule_to_dict_uses_the_app_field_names(self):
        schedule = EventSchedule(month=10, year=2026, events=[
            EventEntry(title="Rapid Respawn", description="Faster", start_date=datetime.date(2026, 10, 3),
                       end_date=datetime.date(2026, 10, 5), color="#fff"),
            EventEntry(title="Open ended", description="", start_date=None, end_date=datetime.date(2026, 10, 2)),
        ])

        result = schedule_to_dict(schedule)

        self.assertEqual(2026, result["year"])
        self.assertEqual(10, result["month"])
        first, second = result["events"]
        self.assertEqual("2026-10-03", first["startDate"])
        self.assertEqual("2026-10-05", first["endDate"])
        self.assertEqual(3, first["duration"])
        self.assertIsNone(second["startDate"])
        self.assertIsNone(second["duration"])

    def test_build_events_snapshot_is_json_serializable(self):
        now = datetime.datetime(2026, 10, 24, 12, 0, tzinfo=datetime.timezone.utc)
        schedule = EventSchedule(month=10, year=2026, events=[])

        snapshot = build_events_snapshot([schedule], now)

        self.assertEqual("2026-10-24T12:00:00+00:00", snapshot["generatedAt"])
        self.assertEqual(1, len(json.loads(json.dumps(snapshot))["schedules"]))
