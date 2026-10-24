"""Builds the daily Char Bazaar snapshot consumed by the ``/exevo/auctions`` endpoint.

The snapshot is only rebuilt once per server save. Every run first checks whether it should do anything, so the
workflow can safely be scheduled several times after the server save to tolerate delays and maintenance.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Optional

import tibiapy
from tibiapy.enums import AuctionOrderBy, AuctionOrderDirection
from tibiapy.errors import ForbiddenError, NetworkError, SiteMaintenanceError
from tibiapy.exevo import (
    auction_to_exevo,
    dump_snapshot,
    last_server_save,
    load_snapshot,
    world_to_server_data,
)
from tibiapy.models import Auction, AuctionFilters

log = logging.getLogger("bazaar_sync")

REQUEST_DELAY = 0.7
CHECKPOINT_EVERY = 100
MAX_ATTEMPTS = 5


class NotReady(Exception):
    """The snapshot doesn't need to (or can't yet) be rebuilt."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", help="Path or URL of the previous snapshot.")
    parser.add_argument("--out", required=True, type=Path, help="Where to write the new snapshot.")
    parser.add_argument("--limit", type=int, help="Debug: maximum number of auctions to fetch details for.")
    parser.add_argument("--max-pages", type=int, help="Debug: maximum number of list pages to scan.")
    parser.add_argument("--max-minutes", type=float, default=270, help="Stop fetching details after this long.")
    parser.add_argument("--force", action="store_true", help="Skip the server save readiness checks.")
    parser.add_argument("--require-complete", action="store_true", help="Exit with an error if not complete.")
    return parser.parse_args()


def _read_previous(source: Optional[str]) -> Optional[dict[str, Any]]:
    if not source:
        return None
    try:
        if source.startswith(("http://", "https://")):
            with urllib.request.urlopen(source, timeout=60) as response:  # noqa: S310
                return load_snapshot(response.read())
        return load_snapshot(Path(source).read_bytes())
    except Exception as e:  # noqa: BLE001
        log.warning("Could not load previous snapshot (%s): %s", source, e)
        return None


async def _retry(func, *args, **kwargs):
    """Call a client method, retrying with exponential backoff when rate-limited."""
    for attempt in range(MAX_ATTEMPTS):
        try:
            result = await func(*args, **kwargs)
            await asyncio.sleep(REQUEST_DELAY)
            return result
        except SiteMaintenanceError:
            raise
        except (ForbiddenError, NetworkError) as e:
            if attempt == MAX_ATTEMPTS - 1:
                raise
            delay = 5 * 2 ** attempt
            log.warning("%s, retrying in %ds", e, delay)
            await asyncio.sleep(delay)


async def _check_ready(client: tibiapy.Client, save: datetime.datetime, force: bool) -> None:
    """Make sure the server save has already been processed by the bazaar."""
    if force:
        return
    filters = AuctionFilters(order_by=AuctionOrderBy.END_DATE, order=AuctionOrderDirection.LOWEST_EARLIEST)
    response = await _retry(client.fetch_current_auctions, 1, filters)
    bazaar = response.data
    if bazaar is None or not bazaar.entries:
        raise NotReady("the bazaar list is empty")
    earliest = min(a.auction_end for a in bazaar.entries)
    if earliest.tzinfo is None:
        earliest = earliest.replace(tzinfo=datetime.timezone.utc)
    if earliest <= save:
        raise NotReady(f"server save not processed yet (earliest auction ends {earliest.isoformat()})")


async def _scan_list(client: tibiapy.Client, max_pages: Optional[int]) -> list[Auction]:
    auctions: dict[int, Auction] = {}
    page = 1
    total_pages = 1
    while page <= total_pages and (max_pages is None or page <= max_pages):
        response = await _retry(client.fetch_current_auctions, page)
        bazaar = response.data
        if bazaar is None:
            break
        total_pages = bazaar.total_pages
        for entry in bazaar.entries:
            auctions[entry.auction_id] = entry
        log.info("List page %d/%d (%d auctions)", page, total_pages, len(auctions))
        page += 1
    return list(auctions.values())


async def _fetch_details(client: tibiapy.Client, auction_id: int) -> Optional[Auction]:
    response = await _retry(client.fetch_auction, auction_id)
    auction = response.data
    if auction is None or auction.details is None:
        return None
    store_items = auction.details.store_items
    if store_items.total_pages > 1:
        await _retry(client._fetch_all_pages, auction_id, store_items, 1)  # noqa: SLF001
    return auction


def _snapshot(save: datetime.datetime, worlds: dict[str, Any], auctions: dict[int, dict], complete: bool) -> dict:
    return {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "lastServerSave": save.isoformat(),
        "complete": complete,
        "worlds": worlds,
        "auctions": sorted(auctions.values(), key=lambda a: a["auctionEnd"]),
    }


async def run(args: argparse.Namespace) -> bool:
    """Run the sync. Returns whether the snapshot is complete."""
    save = last_server_save()
    previous = _read_previous(args.previous)
    if previous and previous.get("complete") and previous.get("lastServerSave") == save.isoformat() \
            and not args.force:
        raise NotReady("snapshot is already up to date")

    client = tibiapy.Client()
    try:
        await _check_ready(client, save, args.force)

        overview = await _retry(client.fetch_world_overview)
        worlds = {w.name: world_to_server_data(w) for w in overview.data.worlds}

        summaries = await _scan_list(client, args.max_pages)
        if not summaries:
            raise NotReady("no auctions found")
        log.info("%d active auctions", len(summaries))

        known = {a["id"]: a for a in (previous or {}).get("auctions", []) if a.get("detailed")}
        result: dict[int, dict] = {}
        pending: list[Auction] = []
        for summary in summaries:
            old = known.get(summary.auction_id)
            if old is not None:
                # Only the bid can have changed since the details were fetched.
                old["currentBid"] = summary.bid
                old["hasBeenBidded"] = summary.bid_type.name != "MINIMUM"
                result[summary.auction_id] = old
            else:
                result[summary.auction_id] = auction_to_exevo(summary, worlds.get(summary.world))
                pending.append(summary)
        log.info("%d reused, %d need details", len(result) - len(pending), len(pending))

        deadline = time.monotonic() + args.max_minutes * 60
        fetched = 0
        for summary in pending:
            if args.limit is not None and fetched >= args.limit:
                break
            if time.monotonic() > deadline:
                log.warning("Time budget reached, publishing a partial snapshot")
                break
            try:
                detailed = await _fetch_details(client, summary.auction_id)
            except SiteMaintenanceError:
                raise
            except NetworkError as e:
                log.warning("Skipping auction %d: %s", summary.auction_id, e)
                continue
            except Exception:  # noqa: BLE001
                # A page the parser can't handle must not take down the whole run. The auction keeps its summary
                # data, is flagged so it doesn't block completion, and is retried on the next run.
                log.exception("Could not parse auction %d", summary.auction_id)
                result[summary.auction_id]["detailFailed"] = True
                fetched += 1
                continue
            if detailed is not None:
                result[summary.auction_id] = auction_to_exevo(detailed, worlds.get(detailed.world))
            fetched += 1
            if fetched % CHECKPOINT_EVERY == 0:
                args.out.write_bytes(dump_snapshot(_snapshot(save, worlds, result, False)))
                log.info("Details %d/%d", fetched, len(pending))
    finally:
        await client.session.close()

    complete = all(a["detailed"] or a.get("detailFailed") for a in result.values())
    args.out.write_bytes(dump_snapshot(_snapshot(save, worlds, result, complete)))
    log.info("Wrote %s (complete=%s, %d auctions)", args.out, complete, len(result))
    return complete


def main() -> int:
    """Entry point. Returns the process exit code."""
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s")
    args = _parse_args()
    try:
        complete = asyncio.run(run(args))
    except NotReady as e:
        log.info("Nothing to do: %s", e)
        return 1 if args.require_complete and "up to date" not in str(e) else 0
    except (SiteMaintenanceError, ForbiddenError) as e:
        log.warning("Tibia.com unavailable: %s", e)
        return 1 if args.require_complete else 0
    if args.require_complete and not complete:
        log.error("Snapshot is not complete")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
