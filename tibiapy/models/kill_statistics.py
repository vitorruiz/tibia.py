from typing import Dict, List

from pydantic import BaseModel

from tibiapy.urls import get_kill_statistics_url


class RaceEntry(BaseModel):
    """Represents the statistics of a race."""

    last_day_killed: int = 0
    """Number of creatures of this race killed in the last day."""
    last_day_players_killed: int = 0
    """Number of players killed by this race in the last day."""
    last_week_killed: int = 0
    """Number of creatures of this race killed in the last week."""
    last_week_players_killed: int = 0
    """Number of players killed by this race in the last week."""


class KillStatistics(BaseModel):
    """Represents the kill statistics of a world."""

    world: str
    """The world the statistics belong to."""
    entries: Dict[str, RaceEntry]
    """A dictionary of kills entries of every race, where the key is the name of the race."""
    total: RaceEntry
    """The kill statistics totals."""
    available_worlds: List[str]
    """The list of worlds available for selection."""

    @property
    def url(self):
        """:class:`str`: The URL to the kill statistics page on Tibia.com containing the results."""
        return get_kill_statistics_url(self.world)

    @property
    def players(self):
        """:class:`RaceEntry`: The kill statistics for players."""
        return self.entries.get("players", RaceEntry())

