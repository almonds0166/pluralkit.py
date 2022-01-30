
from string import ascii_lowercase as ALPHABET
from enum import Enum
from datetime import datetime, timedelta, tzinfo
import re
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)

import pytz
import colour
from .errors import *

# Enums

class Privacy(Enum):
    """Represents the privacies accepted by PluralKit.
    """
    PUBLIC = "public"
    PRIVATE = "private"
    #UNKNOWN = None # legacy, effectively resets privacy to "public"

class AutoproxyMode(Enum):
    """Represents a system's autoproxy mode for `SystemGuildSettings`.
    """
    OFF = 1
    FRONT = 2
    LATCH = 3
    MEMBER = 4

# Base class for all models

class Model:
    """Base class for all models.
    """

    # @classmethod
    # def from_json(cls, obj: dict):
    #     """Convert the given JSON object to an instance of this model class.

    #     Throws a TypeError if the given object is invalid for the given class.

    #     Args:
    #         obj: The JSON object to parse.
    #     """
    #     return Model()

    def json(self):
        """Return the JSON object representing this model.
        """
        return None

# IDs

class PluralKitId(Model):
    """Base class for PluralKit IDs
    """
    id_: str
    uuid: str

    __slots__ = ["id_", "uuid"]

    def __init__(self, id_, uuid):
        assert len(id_) == 5 and all(c in ALPHABET for c in id_), \
            f"{self.CONTEXT} ID should be a five-character lowercase string"

        object.__setattr__(self, "id_", id_)
        object.__setattr__(self, "uuid", uuid)

    def __setattr__(self, name, value):
        msg = f"cannot assign to field {name!r}"
        raise AttributeError(msg)

    def __str__(self):
        return f"{self.id_}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id_}, {self.uuid})"

    json = __str__

class MemberId(PluralKitId):
    """Member IDs
    """
    CONTEXT = "Member"

class SystemId(PluralKitId):
    """System IDs
    """
    CONTEXT = "System"

class SwitchId(PluralKitId):
    """Switch IDs
    """
    CONTEXT = "Switch"

class GroupId(PluralKitId):
    """Group IDs
    """
    CONTEXT = "Group"

# Primitives

class Color(colour.Color, Model):
    """Represents a color.

    This class is initialized in the same way that a `colour.Color`_ object is. It may also take a
    `colour.Color`_ object directly.
    
    .. _`colour.Color`: https://pypi.org/project/colour/#instantiation
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            args = args[0]
            if isinstance(arg, colour.Color):
                colour.Color.__init__(self, args[0].hex_l)
            elif isinstance(arg, str):
                # add octothorp to string if not there
                pattern = r"^([A-Fa-f0-9]{6})$"
                if re.search(pattern, arg):
                    arg = "#" + arg
                colour.Color.__init__(self, arg)
            return

        colour.Color.__init__(self, *args, *kwargs)

    def json(self):
        return self.hex_l[1:]

class Timestamp(Model):
    """Represents a PluralKit UTC timestamp.

    This class works by wrapping around a `datetime` object. To access it, use ``ts.datetime``, for
    any `Timestamp` ``ts``.

    This class may be initialized in the same way that a `datetime` object is. It may also take a
    `datetime` object directly.
    """
    def __init__(self, dt: Optional[datetime]=None, *,
        year: Optional[int]=None,
        month: Optional[int]=None,
        day: Optional[int]=None,
        hour: int=0,
        minute: int=0,
        second: int=0,
        microsecond: int=0
    ):
        if dt is None and any(arg is None for arg in (year, month, day)):
            msg = (
                f"{self.__class__.__name__} is missing required arguments. Either provide a "
                f"datetime.datetime or ISO 8601 formatted string via the first positional "
                f"argument, or provide the year, month, and day through the respective keyword "
                f"arguments."
            )
            raise TypeError(msg)

        if dt is not None:
            if isinstance(dt, datetime):
                if dt.tzinfo is not None:
                    self.datetime = dt.astimezone(pytz.utc)
                else:
                    self.datetime = dt.replace(tzinfo=pytz.utc)
            elif isinstance(dt, str):
                self.datetime = datetime.strptime(bd, r"%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                msg = (
                    f"{self.__class__.__name__} takes either a datetime.datetime object or "
                    f"ISO 8601 formatted string as the first positional argument. Given "
                    f"type(dt)={type(dt)!r}"
                )
                raise TypeError(msg)

        else:
            self.datetime = datetime(year, month, day, hour, minute, second, microsecond)
            self.datetime = self.datetime.replace(tzinfo=pytz.utc)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.json()}>"

    def __str__(self):
        return (
            f"{self.year:04d}-{self.month:02d}-{self.day:02d} "
            f"{self.hour:02d}:{self.minute:02d}:{self.second:02d} UTC"
        )
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.json() == other.json()
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime == other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime == other

        return NotImplemented
    
    def __ne__(self, other):
        x = self.__eq__(other)

        if x is NotImplemented:
            return NotImplemented
        else:
            return not x

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime < other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime < other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime < other

        return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime <= other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime <= other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime <= other

        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime > other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime > other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime > other

        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime >= other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime >= other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime >= other

        return NotImplemented

    @property
    def year(self):
        return self.datetime.year

    @year.setter
    def year(self, value):
        self.datetime = self.datetime.replace(year=value)

    @property
    def month(self):
        return self.datetime.month

    @month.setter
    def month(self, value):
        self.datetime = self.datetime.replace(month=value)

    @property
    def day(self):
        return self.datetime.day

    @day.setter
    def day(self, value):
        self.datetime = self.datetime.replace(day=value)

    @property
    def hour(self):
        return self.datetime.hour

    @hour.setter
    def hour(self, value):
        self.datetime = self.datetime.replace(hour=value)

    @property
    def minute(self):
        return self.datetime.minute

    @minute.setter
    def minute(self, value):
        self.datetime = self.datetime.replace(minute=value)

    @property
    def second(self):
        return self.datetime.second

    @second.setter
    def second(self, value):
        self.datetime = self.datetime.replace(second=value)

    @property
    def microsecond(self):
        return self.datetime.microsecond

    @microsecond.setter
    def microsecond(self, value):
        self.datetime = self.datetime.replace(microsecond=value)

    def json(self) -> str:
        """Convert this timestamp to the ISO 8601 format that PluralKit uses internally.
        """
        return (
            f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
            f"T{self.hour:02d}:{self.minute:02d}:{self.second:02d}.{self.microsecond:06d}Z"
        )

class Birthday(Timestamp):
    """Represents a birthday.
    """
    def __str__(self):
        if self.hidden_year:
            return self.datetime.strftime("%b %d")
        else:
            return self.datetime.strftime("%b %d, ") + f"{self.year:04d}"

    @property
    def hidden_year(self) -> bool:
        """Whether this birthday's year is hidden.

        If set to ``False``, sets the birthday's year to ``0001``, `which internally represents a
        hidden year in PluralKit's API`_.

        .. _`which internally represents a hidden year in PluralKit's API`:
            https://pluralkit.me/api/#member-model
        """
        return self.year in (1, 4)

    @hidden_year.setter
    def hidden_year(self, value: bool):
        if value == True:
            self.year = 1
        else:
            pass # nothing one can do ?

    @staticmethod
    def from_json(bd: str):
        """Takes in a string (as returned by the API) and returns the `Birthday`.

        Args:
            bd: The ``YYYY-MM-DD`` formatted string representing the birthdate.

        Returns:
            Birthday: The corresponding birthday.
        """
        return Birthday(datetime.strptime(bd, r"%Y-%m-%d"))

    def json(self) -> str:
        """Returns the ``YYYY-MM-DD`` formatted birthdate.
        """
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

class Timezone(Model):
    """Represents a tzdb time zone.

    This class is initialized in the same way that `pytz.timezone`_ initializes `tzinfo` objects.
    It may also take a `tzinfo` object directly.

    Hint:
        `Here is a link to a list of tz database time zones`_

    Args:
        tz (Union[str,tzinfo]): The timezone, either as a string or as a `tzinfo` (e.g. from
            `pytz.timezone`_).

    .. _`pytz.timezone`: http://pytz.sourceforge.net/
    .. _`Here is a link to a list of tz database time zones`:
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    """
    def __init__(self, tz):
        if isinstance(tz, tzinfo):
            self.tz = tz
        else:
            self.tz = pytz.timezone(tz)

    def __eq__(self, other):
        return self.tz.zone == other.tz.zone

    def __repr__(self):
        return f"{self.__class__.__name__}({self.tz.zone!r})"

    def json(self):
        """Returns the string representation of this timezone as expected by the API.
        """
        return self.tz.zone

# Settings

class MemberGuildSettings(Model):
    """
    """

class SystemGuildSettings(Model):
    """
    """

# Proxy tags

class ProxyTag(Model):
    """
    """

class ProxyTags(Model):
    """
    """

# Member, System, Group, Switch

class Member(Model):
    """
    """

class System(Model):
    """
    """

class Group(Model):
    """
    """

class Switch(Model):
    """
    """
