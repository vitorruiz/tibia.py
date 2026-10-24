"""Builds the event calendar snapshot (previous, current and next month) consumed by the Tibia Companion app.

It makes only three requests. If Tibia.com refuses any of them, nothing is written, so the last published file stays.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import sys
from pathlib import Path

import tibiapy
from tibiapy.errors import NetworkError
from tibiapy.events_snapshot import build_events_snapshot, months_around

log = logging.getLogger("events_sync")

REQUEST_DELAY = 1.0


async def run(out: Path) -> None:
    """Fetch the three monthly schedules and write the snapshot."""
    now = datetime.datetime.now(datetime.timezone.utc)
    client = tibiapy.Client()
    schedules = []
    try:
        for year, month in months_around(now.date()):
            response = await client.fetch_event_schedule(month, year)
            if response.data is None:
                raise NetworkError(f"No event schedule returned for {year}-{month:02d}")
            schedules.append(response.data)
            log.info("Fetched %d-%02d (%d events)", year, month, len(response.data.events))
            await asyncio.sleep(REQUEST_DELAY)
    finally:
        await client.session.close()
    out.write_text(json.dumps(build_events_snapshot(schedules, now), ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("Wrote %s", out)


def main() -> int:
    """Entry point. Returns the process exit code."""
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        asyncio.run(run(args.out))
    except NetworkError as e:
        log.error("Could not fetch the event calendar: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
