"""Conversion and querying of Char Bazaar auctions using the Exevo Pan JSON format.

The Tibia Companion app consumed the Exevo Pan API. This module produces the same JSON structure from auctions parsed
by this library, and implements the filtering and pagination of ``/auctions`` over an in-memory snapshot.
"""
from __future__ import annotations

import datetime
import gzip
import json
import re
from collections.abc import Iterable
from typing import Any, Optional
from zoneinfo import ZoneInfo

from tibiapy.enums import BattlEyeType, PvpType, Sex, Vocation, WorldLocation
from tibiapy.models import Auction, WorldEntry

__all__ = (
    "SERVER_SAVE_TIMEZONE",
    "auction_to_exevo",
    "build_response",
    "dump_snapshot",
    "filter_auctions",
    "last_server_save",
    "load_snapshot",
    "world_to_server_data",
)

SERVER_SAVE_TIMEZONE = ZoneInfo("Europe/Berlin")
SERVER_SAVE_HOUR = 10

MANY_CHARMS = 15
MANY_QUESTS = 40
MANY_STORE_COSMETICS = 10
SECONDARY_SKILL_MIN = 90.0

VOCATION_IDS = {
    Vocation.NONE: 0,
    Vocation.KNIGHT: 1,
    Vocation.ELITE_KNIGHT: 1,
    Vocation.PALADIN: 2,
    Vocation.ROYAL_PALADIN: 2,
    Vocation.SORCERER: 3,
    Vocation.MASTER_SORCERER: 3,
    Vocation.DRUID: 4,
    Vocation.ELDER_DRUID: 4,
    Vocation.MONK: 5,
    Vocation.EXALTED_MONK: 5,
}

LOCATION_IDS = {
    WorldLocation.EUROPE: 0,
    WorldLocation.NORTH_AMERICA: 1,
    WorldLocation.SOUTH_AMERICA: 2,
    WorldLocation.OCEANIA: 3,
}

PVP_IDS = {
    PvpType.OPTIONAL_PVP: 0,
    PvpType.OPEN_PVP: 1,
    PvpType.RETRO_OPEN_PVP: 2,
    PvpType.HARDCORE_PVP: 3,
    PvpType.RETRO_HARDCORE_PVP: 4,
}

SKILL_KEYS = {
    "axe": "axe",
    "club": "club",
    "distance": "distance",
    "fishing": "fishing",
    "fist": "fist",
    "magic": "magic",
    "shielding": "shielding",
    "sword": "sword",
}

_OUTFIT_ID_REGEX = re.compile(r"/outfits/(\w+)\.gif")


def last_server_save(now: Optional[datetime.datetime] = None) -> datetime.datetime:
    """Get the most recent server save (10:00 CET/CEST) that happened before ``now``, in UTC."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    local = now.astimezone(SERVER_SAVE_TIMEZONE)
    save = local.replace(hour=SERVER_SAVE_HOUR, minute=0, second=0, microsecond=0)
    if save > local:
        save = (local - datetime.timedelta(days=1)).replace(hour=SERVER_SAVE_HOUR, minute=0, second=0, microsecond=0)
    return save.astimezone(datetime.timezone.utc)


def world_to_server_data(world: WorldEntry) -> dict[str, Any]:
    """Convert a world into the ``serverData`` object of Exevo Pan."""
    return {
        "battleye": world.battleye_type == BattlEyeType.INITIALLY_PROTECTED,
        "experimental": world.is_experimental,
        "pvpType": {"type": PVP_IDS.get(world.pvp_type, 0), "string": world.pvp_type.value},
        "serverId": 0,
        "serverLocation": {"type": LOCATION_IDS.get(world.location, 0), "string": world.location.value},
        "serverName": world.name,
    }


def _skill_key(name: str) -> Optional[str]:
    lowered = name.lower()
    return next((key for key in SKILL_KEYS if lowered.startswith(key)), None)


def _skills(auction: Auction) -> dict[str, float]:
    skills = dict.fromkeys(SKILL_KEYS, 0.0)
    if auction.details is None:
        return skills
    for skill in auction.details.skills:
        key = _skill_key(skill.name)
        if key:
            skills[key] = round(skill.level + skill.progress / 100, 2)
    return skills


def _gems(auction: Auction) -> tuple[dict[str, int], list[str]]:
    counts = {"lesser": 0, "regular": 0, "greater": 0}
    greater_mods: list[str] = []
    if auction.details is None:
        return counts, greater_mods
    for gem in auction.details.revealed_gems:
        gem_type = gem.gem_type.lower()
        for tier in counts:
            if tier in gem_type:
                counts[tier] += 1
                if tier == "greater":
                    greater_mods.extend(gem.mods)
                break
    return counts, greater_mods


def _tags(auction: Auction, skills: dict[str, float]) -> list[str]:
    details = auction.details
    if details is None:
        return []
    tags = []
    quests = [q.lower() for q in details.completed_quest_lines]
    if any("soul war" in q for q in quests):
        tags.append("soulwarAvailable")
    if any("primal" in q for q in quests):
        tags.append("primalAvailable")
    if len(details.charms) >= MANY_CHARMS:
        tags.append("manyCharms")
    if len(quests) >= MANY_QUESTS:
        tags.append("manyQuests")
    if len(details.store_mounts.entries) + len(details.store_outfits.entries) >= MANY_STORE_COSMETICS:
        tags.append("manyStoreCosmetics")
    if VOCATION_IDS.get(auction.vocation) == 1:
        weapons = sorted((skills["axe"], skills["club"], skills["sword"]), reverse=True)
        if weapons[1] >= SECONDARY_SKILL_MIN:
            tags.append("secondaryEkSkill")
    return tags


def auction_to_exevo(auction: Auction, server_data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Convert an auction into the Exevo Pan auction format.

    If the auction has no details, the detailed fields are left empty and ``detailed`` is false, so it can be
    completed on a later run.
    """
    details = auction.details
    skills = _skills(auction)
    gem_counts, greater_mods = _gems(auction)
    outfit_match = _OUTFIT_ID_REGEX.search(auction.outfit.image_url)
    now = datetime.datetime.now(datetime.timezone.utc)
    transfer_date = details.regular_world_transfer_available_date if details else None
    has_transfer = details is not None and (transfer_date is None or _as_utc(transfer_date) <= now)
    return {
        "id": auction.auction_id,
        "nickname": auction.name,
        "level": auction.level,
        "vocationId": VOCATION_IDS.get(auction.vocation, 0),
        "sex": auction.sex == Sex.MALE,
        "outfitId": outfit_match.group(1) if outfit_match else str(auction.outfit.outfit_id),
        "auctionEnd": int(_as_utc(auction.auction_end).timestamp()),
        "currentBid": auction.bid,
        "hasBeenBidded": auction.bid_type.name != "MINIMUM",
        "items": [float(f"{item.item_id}.{item.tier}") for item in auction.displayed_items],
        "serverData": server_data or {"serverName": auction.world},
        "detailed": details is not None,
        "skills": skills,
        "achievementPoints": details.achievement_points if details else 0,
        "bossPoints": details.boss_points if details else 0,
        "charmInfo": {
            "expansion": details.charm_expansion if details else False,
            "total": (details.available_charm_points + details.spent_charm_points) if details else 0,
            "unspent": details.available_charm_points if details else 0,
        },
        "charms": [c.name for c in details.charms] if details else [],
        "gems": gem_counts,
        "greaterGems": greater_mods,
        "hirelings": {
            "count": details.hirelings if details else 0,
            "jobs": details.hireling_jobs if details else 0,
            "outfits": details.hireling_outfits if details else 0,
        },
        "huntingSlot": bool(details and details.permanent_hunting_task_slots > 0),
        "preySlot": bool(details and details.permanent_prey_slots > 0),
        "imbuements": list(details.imbuements) if details else [],
        "mounts": [m.name for m in details.mounts.entries] if details else [],
        "outfits": [{"name": o.name, "type": o.addons} for o in details.outfits.entries] if details else [],
        "quests": list(details.completed_quest_lines) if details else [],
        "rareAchievements": [],
        "storeItems": [{"name": i.name, "amount": i.count} for i in details.store_items.entries] if details else [],
        "storeMounts": [m.name for m in details.store_mounts.entries] if details else [],
        "storeOutfits": [{"name": o.name, "type": o.addons} for o in details.store_outfits.entries] if details else [],
        "tags": _tags(auction, skills),
        "tcInvested": 0,
        "transfer": has_transfer,
        "serverId": 0,
    }


def _as_utc(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc)


def dump_snapshot(snapshot: dict[str, Any]) -> bytes:
    """Serialize a snapshot into gzipped JSON."""
    return gzip.compress(json.dumps(snapshot, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def load_snapshot(data: bytes) -> dict[str, Any]:
    """Load a snapshot from gzipped (or plain) JSON bytes."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return json.loads(data)


def filter_auctions(  # noqa: PLR0912
        auctions: Iterable[dict[str, Any]],
        *,
        auction_ids: Optional[list[int]] = None,
        battleye: Optional[list[bool]] = None,
        location: Optional[list[int]] = None,
        max_level: Optional[int] = None,
        min_level: Optional[int] = None,
        min_skill: Optional[int] = None,
        pvp: Optional[list[int]] = None,
        server_set: Optional[list[str]] = None,
        skill_key: Optional[list[str]] = None,
        transfer_available: Optional[bool] = None,
        vocation: Optional[list[int]] = None,
        nickname: Optional[str] = None,
        now: Optional[datetime.datetime] = None,
) -> list[dict[str, Any]]:
    """Filter auctions with the same semantics of the Exevo Pan ``/auctions`` endpoint.

    Ended auctions are always left out. Results are sorted by end date, soonest first.
    """
    now_ts = (now or datetime.datetime.now(datetime.timezone.utc)).timestamp()
    ids = set(auction_ids or [])
    servers = {s.lower() for s in server_set or []}
    keys = [k for k in skill_key or [] if k in SKILL_KEYS]
    needle = nickname.lower() if nickname else None
    results = []
    for auction in auctions:
        if auction["auctionEnd"] <= now_ts:
            continue
        server = auction.get("serverData", {})
        if ids and auction["id"] not in ids:
            continue
        if servers and server.get("serverName", "").lower() not in servers:
            continue
        if location and server.get("serverLocation", {}).get("type") not in location:
            continue
        if pvp and server.get("pvpType", {}).get("type") not in pvp:
            continue
        if battleye and bool(server.get("battleye")) not in battleye:
            continue
        if vocation and auction["vocationId"] not in vocation:
            continue
        if min_level is not None and auction["level"] < min_level:
            continue
        if max_level is not None and auction["level"] > max_level:
            continue
        if min_skill is not None and keys and not any(auction["skills"].get(k, 0) >= min_skill for k in keys):
            continue
        if transfer_available is not None and auction.get("transfer") != transfer_available:
            continue
        if needle and needle not in auction["nickname"].lower():
            continue
        results.append(auction)
    results.sort(key=lambda a: a["auctionEnd"])
    return results


def build_response(results: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    """Paginate the results (zero-based page) in the Exevo Pan response format."""
    start = page * page_size
    end = min(start + page_size, len(results))
    return {
        "descendingOrder": False,
        "endOffset": end,
        "hasNext": end < len(results),
        "hasPrev": page > 0,
        "page": results[start:end],
        "pageIndex": page,
        "sortingMode": 0,
        "startOffset": start,
        "totalItems": len(results),
    }
