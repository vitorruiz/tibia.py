from __future__ import annotations

import datetime
from typing import List, Optional, TYPE_CHECKING

from tibiapy import TransferType, BattlEyeType
from tibiapy.models.world import World, WorldEntry, WorldOverview

if TYPE_CHECKING:
    from tibiapy.models import OnlineCharacter
    from tibiapy import WorldLocation, PvpType

__all__ = (
    "WorldBuilder",
    "WorldEntryBuilder",
    "WorldOverviewBuilder"
)

class WorldEntryBuilder:
    def __init__(self):
        self._name = None
        self._online = None
        self._location = None
        self._pvp_type = None
        self._online_count = 0
        self._transfer_type = TransferType.REGULAR
        self._battleye_date = None
        self._battleye_type = BattlEyeType.UNPROTECTED
        self._experimental = False
        self._premium_only = False

    def name(self, name: str):
        self._name = name
        return self

    def online(self, online: bool):
        self._online = online
        return self

    def online_count(self, online_count: int):
        self._online_count = online_count
        return self

    def location(self, location: WorldLocation):
        self._location = location
        return self

    def pvp_type(self, pvp_type: PvpType):
        self._pvp_type = pvp_type
        return self

    def premium_only(self, premium_only: bool):
        self._premium_only = premium_only
        return self

    def transfer_type(self, transfer_type: TransferType):
        self._transfer_type = transfer_type
        return self


    def battleye_date(self, battleye_date: Optional[datetime.datetime]):
        self._battleye_date = battleye_date
        return self

    def battleye_type(self, battleye_type: BattlEyeType):
        self._battleye_type = battleye_type
        return self

    def experimental(self, experimental: bool):
        self._experimental = experimental
        return self

    def build(self):
        return WorldEntry(
            name=self._name,
            online=self._online,
            online_count=self._online_count,
            location=self._location,
            pvp_type=self._pvp_type,
            premium_only=self._premium_only,
            transfer_type=self._transfer_type,
            battleye_date=self._battleye_date,
            battleye_type=self._battleye_type,
            experimental=self._experimental,
        )


class WorldBuilder(WorldEntryBuilder):
    def __init__(self):
        super().__init__()
        self._record_count = None
        self._record_date = None
        self._creation_date = None
        self._online_players = []
        self._world_quest_titles = []
    def record_count(self, record_count: int):
        self._record_count = record_count
        return self

    def record_date(self, record_date: datetime.datetime):
        self._record_date = record_date
        return self

    def creation_date(self, creation_date: str):
        self._creation_date = creation_date
        return self

    def world_quest_titles(self, world_quest_titles: List[str]):
        self._world_quest_titles = world_quest_titles
        return self

    def add_world_quest_title(self, world_quest_title: str):
        self._world_quest_titles.append(world_quest_title)
        return self

    def online_players(self, online_players: List[OnlineCharacter]):
        self._online_players = online_players
        return self

    def add_online_player(self, player: OnlineCharacter):
        self._online_players.append(player)
        return self

    def build(self):
        return World(
            name=self._name,
            online=self._online,
            online_count=self._online_count,
            record_count=self._record_count,
            record_date=self._record_date,
            creation_date=self._creation_date,
            location=self._location,
            pvp_type=self._pvp_type,
            premium_only=self._premium_only,
            transfer_type=self._transfer_type,
            world_quest_titles=self._world_quest_titles,
            battleye_date=self._battleye_date,
            battleye_type=self._battleye_type,
            experimental=self._experimental,
            online_players=self._online_players,
        )



class WorldOverviewBuilder:
    def __init__(self, **kwargs) -> None:
        self._record_count = kwargs.get("record_count")
        self._record_date = kwargs.get("record_date")
        self._worlds = kwargs.get("worlds")

    def record_count(self, record_count: int):
        self._record_count = record_count
        return self

    def record_date(self, record_date: datetime.datetime):
        self._record_date = record_date
        return self

    def worlds(self, worlds: List[WorldEntry]):
        self._worlds = worlds
        return self

    def build(self):
        return WorldOverview(
            record_count=self._record_count,
            record_date=self._record_date,
            worlds=self._worlds,
        )
