import enum

__all__ = (
    'AccountStatus',
    'Category',
    'HouseOrder',
    'HouseStatus',
    'HouseType',
    'NewsCategory',
    'NewsType',
    'PvpType',
    'Sex',
    'ThreadStatus',
    'TournamentWorldType',
    'TournamentPhase',
    'TransferType',
    'Vocation',
    'VocationFilter',
    'WorldLocation',
)


class BaseEnum(enum.Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return "%s.%s" % (self.__class__.__name__, self.name)


class AccountStatus(BaseEnum):
    """Possible account statuses."""
    FREE_ACCOUNT = "Free Account"
    PREMIUM_ACCOUNT = "Premium Account"


class Category(BaseEnum):
    """The different highscores categories."""
    ACHIEVEMENTS = "achievements"
    AXE_FIGHTING = "axe"
    CLUB_FIGHTING = "club"
    DISTANCE_FIGHTING = "distance"
    EXPERIENCE = "experience"
    FISHING = "fishing"
    FIST_FIGHTING = "fist"
    LOYALTY_POINTS = "loyalty"
    MAGIC_LEVEL = "magic"
    SHIELDING = "shielding"
    SWORD_FIGHTING = "sword"


class HouseOrder(BaseEnum):
    """The possible ordering methods for house lists in Tibia.com"""
    NAME = "name"
    SIZE = "size"
    RENT = "rent"
    BID = "bid"
    AUCTION_END = "end"


class HouseStatus(BaseEnum):
    """Renting statuses of a house."""
    RENTED = "rented"
    AUCTIONED = "auctioned"


class HouseType(BaseEnum):
    """The types of house available."""
    HOUSE = "house"
    GUILDHALL = "guildhall"


class NewsCategory(BaseEnum):
    """The different news categories."""
    CIPSOFT = "cipsoft"
    COMMUNITY = "community"
    DEVELOPMENT = "development"
    SUPPORT = "support"
    TECHNICAL_ISSUES = "technical"


class NewsType(BaseEnum):
    """The different types of new entries."""
    NEWS_TICKER = "News Ticker"
    FEATURED_ARTICLE = "Featured Article"
    NEWS = "News"


class PvpType(BaseEnum):
    """The possible PvP types a World can have."""
    OPEN_PVP = "Open PvP"
    OPTIONAL_PVP = "Optional PvP"
    RETRO_OPEN_PVP = "Retro Open PvP"
    RETRO_HARDCORE_PVP = "Retro Hardcore PvP"
    HARDCORE_PVP = "Hardcore PvP"


class Sex(BaseEnum):
    """Possible character sexes."""
    MALE = "male"
    FEMALE = "female"


class ThreadStatus(enum.Flag):
    """The possible statuses a thread can have."""
    NONE = 0
    HOT = 1  #: Thread has more than 16 replies.
    NEW = 2  #: Thread has new posts since last visit.
    CLOSED = 4  #: Thread is closed.
    STICKY = 8  #: Thread is stickied.

    def __str__(self):
        return ", ".join(v.name.title() for v in list(self))

    def __iter__(self):
        for entry in list(self.__class__):
            if entry in self and entry is not self.NONE:
                yield entry

    def get_icon_name(self):
        if self.value == 0:
            return None
        joined_str = "".join(v.name.lower() for v in list(self))
        return "logo_%s.gif" % joined_str

    @classmethod
    def from_icon(cls, icon):
        flags = 0
        for entry in list(cls):
            if entry.name.lower() in icon:
                flags += entry.value
        return cls(flags)

class TournamentWorldType(BaseEnum):
    """The possible types of tournament worlds."""
    REGUlAR = "Regular"
    RESTRICTED = "Restricted Store"


class TournamentPhase(BaseEnum):
    """The possible tournament phases."""
    SIGN_UP = "sign up"
    RUNNING = "running"
    ENDED = "ended"


class TransferType(BaseEnum):
    """The possible special transfer restrictions a world may have."""
    REGULAR = "regular"  #: No special transfer restrictions
    BLOCKED = "blocked"  #: Can't transfer to this world, but can transfer out of this world.
    LOCKED = "locked"  #: Can transfer to this world, but can't transfer out of this world.


class Vocation(BaseEnum):
    """The possible vocation types."""
    NONE = "None"
    DRUID = "Druid"
    KNIGHT = "Knight"
    PALADIN = "Paladin"
    SORCERER = "Sorcerer"
    ELDER_DRUID = "Elder Druid"
    ELITE_KNIGHT = "Elite Knight"
    ROYAL_PALADIN = "Royal Paladin"
    MASTER_SORCERER = "Master Sorcerer"


class VocationFilter(enum.Enum):
    """The vocation filters available for Highscores."""
    ALL = 0
    KNIGHTS = 1
    PALADINS = 2
    SORCERERS = 3
    DRUIDS = 4

    @classmethod
    def from_name(cls, name, all_fallback=True):
        """Gets a vocation filter from a vocation's name.

        Parameters
        ----------
        name: :class:`str`
            The name of the vocation.
        all_fallback: :class:`bool`
            Whether to return :py:attr:`ALL` if no match is found. Otherwise, ``None`` will be returned.

        Returns
        -------
        VocationFilter, optional:
            The matching vocation filter.
        """
        name = name.upper()
        for vocation in cls:  # type: VocationFilter
            if vocation.name in name or vocation.name[:-1] in name and vocation != cls.ALL:
                return vocation
        if all_fallback or name.upper() == "ALL":
            return cls.ALL
        return None


class WorldLocation(BaseEnum):
    """The possible physical locations for servers."""
    EUROPE = "Europe"
    NORTH_AMERICA = "North America"
    SOUTH_AMERICA = "South America"
