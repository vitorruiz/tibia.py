import abc
import datetime
import json
import urllib.parse
from collections import OrderedDict
from enum import Enum

CHARACTER_URL = "https://www.tibia.com/community/?subtopic=characters&name=%s"
CHARACTER_URL_TIBIADATA = "https://api.tibiadata.com/v2/characters/%s.json"
URL_HOUSE = "https://www.tibia.com/community/?subtopic=houses&page=view&houseid=%d&world=%s"
URL_HOUSE_TIBIADATA = "https://api.tibiadata.com/v2/house/%s/%d.json"


class Serializable(abc.ABC):
    """Implements methods to make a class convertible to JSON.

    Note that there's no way to convert JSON strings back to their original object and that some data might be lost."""
    @classmethod
    def __slots_inherited__(cls):
        slots = []
        for base in cls.__bases__:
            try:
                # noinspection PyUnresolvedReferences
                slots.extend(base.__slots_inherited__())
            except AttributeError:
                continue
        slots.extend(getattr(cls, "__slots__", []))
        return tuple(OrderedDict.fromkeys(slots))

    def keys(self):
        return list(self.__slots_inherited__())

    def __getitem__(self, item):
        if item in self.keys():
            try:
                return getattr(self, item)
            except AttributeError:
                return None
        else:
            raise KeyError(item)

    @staticmethod
    def _try_dict(obj):
        try:
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            return {k:v for k,v in dict(obj).items() if v is not None}
        except TypeError:
            return str(obj)

    def to_json(self, *, indent=None, sort_keys = False):
        """Gets the object's JSON representation.

        Parameters
        ----------
        indent: :class:`int`, optional
            Number of spaces used as indentation, ``None`` will return the shortest possible string.
        sort_keys: :class:`bool`, optional
            Whether keys should be sorted alphabetically or preserve the order defined by the object.

        Returns
        -------
        :class:`str`
            JSON representation of the object.
        """
        return json.dumps({k:v for k,v in dict(self).items() if v is not None}, indent=indent, sort_keys=sort_keys,
                          default=self._try_dict)

class Character(Serializable, metaclass=abc.ABCMeta):
    """Base class for all character classes.

    Implements common properties.

    Attributes
    ----------
    name: :class:`str`
    """
    __slots__ = ("name", )

    def __eq__(self, o: object) -> bool:
        """Two characters are considered equal if their names are equal."""
        if isinstance(o, self.__class__):
            return self.name.lower() == o.name.lower()
        return False

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} name={0.name!r}>".format(self,)

    @property
    def url(self):
        """
        :class:`str`: The URL of the character's information page on Tibia.com
        """
        return self.get_url(self.name)

    @property
    def url_tibiadata(self):
        """
        :class:`str`: The URL of the character's information on TibiaData
        """
        return self.get_url_tibiadata(self.name)

    @classmethod
    def get_url(cls, name):
        """Gets the Tibia.com URL for a given character name.

        Parameters
        ------------
        name: :class:`str`
            The name of the character

        Returns
        --------
        :class:`str`
            The URL to the character's page."""
        return CHARACTER_URL % urllib.parse.quote(name.encode('iso-8859-1'))

    @classmethod
    def get_url_tibiadata(cls, name):
        """Gets the TibiaData.com URL for a given character name.

        Parameters
        ------------
        name: :class:`str`
            The name of the character

        Returns
        --------
        :class:`str`
            The URL to the character's page on TibiaData."""
        return CHARACTER_URL_TIBIADATA % urllib.parse.quote(name.encode('iso-8859-1'))

class House(Serializable, metaclass=abc.ABCMeta):
    __slots__ = ("name", "world", "status", "type")

    @classmethod
    def get_url(cls, house_id, world):
        """ Gets the Tibia.com URL for house with the given id and world.

        Parameters
        ----------
        house_id: :class:`int`
            The internal id of the house.
        world: :class:`str`
            The world of the house.

        Returns
        -------
        The URL to the house in Tibia.com
        """
        return URL_HOUSE % (house_id, world)

    @classmethod
    def get_url_tibiadata(cls, house_id, world):
        """ Gets the TibiaData.com URL for house with the given id and world.

        Parameters
        ----------
        house_id: :class:`int`
            The internal id of the house.
        world: :class:`str`
            The world of the house.

        Returns
        -------
        The URL to the house in TibiaData.com
        """
        return URL_HOUSE_TIBIADATA % (world, house_id)

class HouseWithId(House):
    __slots__ = ("id",)

    @property
    def url(self):
        """:class:`str`: The URL to the Tibia.com page of the house."""
        return self.get_url(self.id, self.world) if self.id and self.world else None

    @property
    def url_tibiadata(self):
        """:class:`str`: The URL to the TibiaData.com page of the house."""
        return self.get_url_tibiadata(self.id, self.world) if self.id and self.world else None