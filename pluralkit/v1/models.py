
from datetime import datetime, timedelta, tzinfo
from enum import Enum
import string
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Generator,
)

import pytz
import colour
from .errors import *

class Privacy(Enum):
    """Represents the privacies accepted by PluralKit.
    """
    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = None # legacy, effectively resets privacy to "public"

class Color(colour.Color):
    """Represents a color.

    This class is initialized in the same way that a `colour.Color`_ object is. It may also take a
    `colour.Color`_ object directly.

    .. _`colour.Color`: https://pypi.org/project/colour/#instantiation
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], colour.Color):
            super().__init__(args[0].hex_l)
        else:
            super().__init__(*args, **kwargs)

    @staticmethod
    def parse(c):
        """Takes in a `Color`, `colour.Color`_, or str and converts to `Color` as
        needed.

        Args:
            color (Union[Color,colour.Color,str,None]): The color, represented as a `Color`,
                `colour.Color`_ or `str`. If a string, may either be in the format as expected by
                PluralKit's API internally (e.g. ``00ffff``) or a color string that can be taken by
                a Color object (e.g. ``cyan``).

        Returns:
            Optional[Color]: The `Color` object, or ``None`` if input is None.

        Raises:
            TypeError: If the given argument is neither a `Color`, `colour.Color`_, or `str`.

        .. _`colour.Color`: https://pypi.org/project/colour/#instantiation
        """
        if c is None: return None

        if isinstance(c, colour.Color):
            return c

        if isinstance(c, str):
            if len(c) == 6 and set(c).issubset(set(string.hexdigits)):
                return Color.from_json(c)
            else:
                return Color(c)

        raise TypeError(
            f"Argument `c` must be of type colour.Color or str; received c={type(c)}."
        )

    @staticmethod
    def from_json(color: str):
        """Takes in a string (as returned by the API) and returns the `Color`.
        """
        return Color(color=f"#{color}") # mypy says this has too many args?

    def json(self):
        """Returns the hex of the `Color` sans the ``#`` symbol.

        Example: ``Color("magenta").json()`` would return ``"ff00ff"``.
        """
        return self.hex_l[1:]

class Timezone:
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
    def __init__(self, *args, **kwargs):
        if len(args) != 1 or len(kwargs) != 0:
            raise TypeError(
                f"Timezone is initialized with exactly one positional argument `tz`; " \
                f"received len(args)={len(args)} and len(args)={len(kwargs)}"
            )
        if isinstance(args[0], tzinfo):
            self.tz = args[0]
        else:
            self.tz = pytz.timezone(args[0])
    
    def __eq__(self, other):
        return self.tz.zone == other.tz.zone
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.zone}>"

    @property
    def zone(self):
        return self.tz.zone

    @staticmethod
    def parse(tz):
        """Takes in a `Timezone`, `tzinfo`, or `str` and converts to `Timezone` as needed.

        Args:
            tz (Union[Timezone,tzinfo,str]): The timezone, represented as a
                `Timezone`, `tzinfo`, or `str`.

        Raises:
            TypeError: If given argument is neither a `Timezone`, `tzinfo`, nor `str`.
        """
        if isinstance(tz, Timezone):
            return tz

        if isinstance(tz, (tzinfo, str)):
            return Timezone(tz)

        raise TypeError(
            f"Argument `tz` must be of type Timezone, tzinfo, or str; " \
            f"received type(tz)={type(tz)}."
        )

    @staticmethod
    def from_json(tz: str):
        """Takes in a string (as returned by the API) and returns the Timezone.

        Args:
            tz: The time zone as stored in the PluralKit API internally.

        Returns:
            Timezone: The corresponding `Timezone` object.
        """
        return Timezone(tz)

    def json(self):
        """Returns the string representation of this timezone as expected by the API.
        """
        return self.zone
    
class Timestamp:
    """Represents a PluralKit UTC timestamp.

    This class works by wrapping around a `datetime` object. Use ts.datetime to access it, for any
    `Timestamp` ts.

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
            raise TypeError(
                f"{self.__class__.__name__} is missing required arguments. Either provide a " \
                f"datetime.datetime via the first positional argument, or provide the year, " \
                f"month, and day through the respective keyword arguments."
            )

        if dt is not None:
            if dt.tzinfo is not None:
                self.datetime = dt.astimezone(pytz.utc)
            else:
                self.datetime = dt.replace(tzinfo=pytz.utc)

        else:
            # mypy complains here
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
        return self.json() == other.json()
    
    def __ne__(self, other):
        return not self.__eq__(other)

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

    @staticmethod
    def parse(ts):
        """Takes in a `Timestamp`, `datetime`_, or `str`, converts to `Timestamp` as needed.

        Args:
            ts (Union[Timestamp,datetime,str]): The timestamp, represented as a `Timestamp`,
                `datetime`_, or `str`.

        Returns:
            Timestamp: The `Timestamp` object.

        Raises:
            TypeError: If given argument is neither a `Timestamp`, `datetime`_, or `str`.

        .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
        """
        if isinstance(ts, Timestamp):
            return ts

        if isinstance(ts, datetime):
            return Timestamp(ts)

        if isinstance(ts, str):
            return Timestamp.from_json(ts)

        raise TypeError(
            f"Argument `ts` must be of type Timestamp, datetime.datetime, or str; " \
            f"received type(ts)={type(ts)}."
        )

    @staticmethod
    def from_json(bd: str):
        """Takes in a string (as returned by the API) and returns the corresponding `Timestamp`.

        Args:
            bd: The ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` formatted
                string representing a PluralKit API timestamp.

        Returns:
            Timestamp: The corresponding `Timestamp` object.
        """
        return Timestamp(datetime.strptime(bd, r"%Y-%m-%dT%H:%M:%S.%fZ"))

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
        self.year = 1

    @staticmethod
    def parse(bd):
        """Takes in a `Birthday`, `datetime`_, or str, converts to `Birthday` as needed.

        Args:
            bd (Union[Birthday,datetime,str,None]): The birthday, represented as a `Birthday`,
                `datetime`_, or str.

        Returns:
            Optional[Birthday]: The `Birthday` object, or ``None`` if input is ``None``.

        Raises:
            TypeError: If given argument is neither a `Birthday`, `datetime`_, or str.

        .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
        """
        if bd is None: return None

        if isinstance(bd, Birthday):
            return bd

        if isinstance(bd, datetime):
            return Birthday(bd)

        if isinstance(bd, str):
            return Birthday.from_json(bd)

        raise TypeError(
            f"Argument `bd` must be None or of type Birthday, datetime.datetime, or str; " \
            f"received type(bd)={type(bd)}."
        )

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

class ProxyTag:
    """Represents a single PluralKit proxy tag.

    Args:
        prefix: Prefix that will enclose proxied messages.
        suffix: Suffix that will enclose proxied messages.

    Important:
        At least one of the ``suffix`` or ``prefix`` arguments must be passed.
    
    Attributes:
        prefix (Optional[str]): Prefix that will enclose proxied messages.
        suffix (Optional[str]): Suffix that will enclose proxied messages.
    """
    def __init__(self, *,
        prefix: Optional[str]=None,
        suffix: Optional[str]=None,
    ):
        assert prefix or suffix, \
            "A valid proxy tag must have at least one of the prefix or suffix defined."
        self.prefix = prefix
        self.suffix = suffix
    
    def __eq__(self, other):
        return self.prefix == other.prefix and self.suffix == other.suffix
    
    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_json(proxy_tag: Dict[str,str]):
        """Static method to convert a proxy tag `dict` to a `ProxyTag`.

        Args:
            proxy_tag: Dictionary representing a proxy tag. Must have at least one of ``prefix`` or
                ``suffix`` as keys.

        Returns:
            ProxyTag: The corresponding `ProxyTag` object.
        """
        return ProxyTag(
            prefix=proxy_tag.get("prefix"),
            suffix=proxy_tag.get("suffix")
        )

    def __repr__(self):
        prefix = "" if not self.prefix else f"prefix={repr(self.prefix)}"
        suffix = "" if not self.suffix else f"suffix={repr(self.suffix)}"
        attrs = ",".join(a for a in (prefix, suffix) if a)
        return (
            f"{self.__class__.__name__}({attrs})"
        )

    def match(self, message: str) -> bool:
        """Determine if a given message would be proxied under this proxy tag.
        
        Args:
            message: Message to parse.
        """
        message = message.strip()
        return (True if not self.prefix else message.startswith(self.prefix)) \
            and (True if not self.suffix else message.endswith(self.suffix))

    def json(self) -> Dict[str,Optional[str]]:
        """Return the JSON object representing this proxy tag as a Python `dict`.
        """
        return {
            "prefix": self.prefix,
            "suffix": self.suffix,
        }

class ProxyTags:
    """Represents a set of PluralKit proxy tags.

    Hint:
        ProxyTags objects can be iterated or indexed to yield its underlying `ProxyTag` objects.    
    
    Args:
        proxy_tags: A sequence of `ProxyTag` objects.
    """
    def __init__(self, proxy_tags: Optional[Generator[ProxyTag,None,None]]=None):
        self._proxy_tags: Tuple[ProxyTag,...]
        if proxy_tags is None:
            self._proxy_tags = tuple()
        else:
            self._proxy_tags = tuple(proxy_tags)

    def __repr__(self):
        return f"{self.__class__.__name__}<{len(self._proxy_tags)}>"

    def __iter__(self):
        for proxy_tag in self._proxy_tags:
            yield proxy_tag

    def __getitem__(self, index):
        return self._proxy_tags[index]
    
    def __eq__(self, other):
        return set(self._proxy_tags) == set(other._proxy_tags)
    
    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_json(proxy_tags: Sequence[Dict[str,str]]):
        """Static method to convert a list of proxy tags `dict`s to a `ProxyTags` object.

        Args:
            proxy_tags: Sequence of Python dictionaries, each representing a proxy tag.

        Returns:
            ProxyTags: The corresponding `ProxyTags` object.
        """
        return ProxyTags(ProxyTag.from_json(proxy_tag) for proxy_tag in proxy_tags)

    def match(self, message: str) -> bool:
        """Determine if a given message would be proxied under this set of proxy tags.
        
        Args:
            message: Message to parse.
        """
        return any(proxy_tag.match(message) for proxy_tag in self)

    def json(self) -> List[Dict[str,str]]:
        """Return the JSON object representing this proxy tag as a list of Python `dict`.
        """
        return [proxy_tag.json() for proxy_tag in self]

class System:
    """Represents a PluralKit system.

    Args:
        id: The system's five-character lowercase ID.
        created: The system's creation date. May be a string formatted as
            ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601 format), a
            `Timestamp`, or a `datetime`_.
        name: The name of the system. Default ``None``.
        description: The description of the system. Default ``None``.
        tag: The system's tag appended to display names. Default ``None``.
        avatar_url: The system's avatar URL. Default ``None``.
        tz: The system's tzdb timezone. May be a `Timezone`, `tzinfo`, or `str`. Default is
            ``"UTC"``.
        description_privacy: The system's description privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        member_list_privacy: The system's member list privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        front_privacy: The system's fronting privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        front_history_privacy: The system's fronting history privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.

    Attributes:
        id (str): The system's five-character lowercase ID.
        name (Optional[str]): The name of the system.
        description (Optional[str]): The description of the system.
        tag (Optional[str]): The system's tag appended to display names.
        avatar_url (Optional[str]): The system's avatar URL.
        tz (Timezone): The system's tzdb timezone.
        created (Timestamp): The system's timestamp at creation.
        description_privacy (Privacy): The system's description privacy.
        member_list_privacy (Privacy): The system's member list privacy.
        front_privacy (Privacy): The system's fronting privacy.
        front_history_privacy (Privacy): The system's fronting history privacy.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """

    def __init__(self, *,
        id: str,
        created: Union[Timestamp,datetime,str],
        name: Optional[str]=None,
        description: Optional[str]=None,
        tag: Optional[str]=None,
        avatar_url: Optional[str]=None,
        tz: Union[Timezone,tzinfo,str]="UTC",
        description_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        member_list_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        front_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        front_history_privacy: Union[Privacy,str]=Privacy.PUBLIC
    ):
        self.id = id
        self.name = name

        self.description = description
        self.tag = tag
        self.avatar_url = avatar_url

        self.created = Timestamp.parse(created)
        self.tz = Timezone.parse(tz)

        self.description_privacy = Privacy(description_privacy)
        self.member_list_privacy = Privacy(member_list_privacy)
        self.front_privacy = Privacy(front_privacy)
        self.front_history_privacy = Privacy(front_history_privacy)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.id}')"

    def __str__(self):
        return self.id
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def _deep_equal(self, other, ignore_id=False) -> bool:
        if ignore_id is False:
            return self.__dict__ == other.__dict__
        elif ignore_id is True:
            self_dict = self.__dict__
            self_dict.pop("id")
            other_dict = other.__dict__
            other_dict.pop("id")
            return self_dict == other_dict
        
    @staticmethod
    def from_json(system: Dict[str,Any]):
        """Static method to convert a system `dict` to a `System` object.

        Args:
            system: Dictionary representing a system, e.g. one received directly from the API. Must
                have a value for the ``id`` and ``created`` attributes.

        Returns:
            System: The corresponding `System` object.
        """
        return System(
            id=system["id"],
            name=system.get("name"),
            description=system.get("description"),
            tag=system.get("tag"),
            avatar_url=system.get("avatar_url"),
            tz=system.get("tz", "UTC"),
            created=system["created"],
            description_privacy=system.get("description_privacy", "public"),
            member_list_privacy=system.get("member_list_privacy", "public"),
            front_privacy=system.get("front_privacy", "public"),
            front_history_privacy=system.get("front_history_privacy", "public")
        )

    def json(self) -> Dict[str,Any]:
        """Return Python `dict` representing this system.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tag": self.tag,
            "avatar_url": self.avatar_url,
            "tz": self.tz.json(),
            "created": self.created.json(),
            "description_privacy": self.description_privacy.value,
            "member_list_privacy": self.member_list_privacy.value,
            "front_privacy": self.front_privacy.value,
            "front_history_privacy": self.front_history_privacy.value
        }
    
class Member:
    """Represents a PluralKit system member.

    Args:
        id: The member's five-letter lowercase ID.
        name: The member's name.
        created: The member's creation date. May be a string formatted as
            ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601 format), a
            `Timestamp`, or a `datetime`_.
        name_privacy: The member's name privacy, either `~Privacy.PUBLIC` or `~Privacy.PRIVATE`.
            Default is public.
        display_name: The member's display name. Default is ``None``.
        description: The member's description. Default is ``None``.
        description_privacy: The member's description privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        color: The member's color. Default is ``None``.
        birthday: The member's birthdate. May be a string formatted as ``{year}-{month}-{day}``, a
            `Timestamp`, or a `datetime`_. Default is ``None``.
        birthday_privacy: The member's birthdate privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        pronouns: The member's pronouns. Default is ``None``.
        pronoun_privacy: The member's pronouns privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        avatar_url: The member's avatar URL.
        avatar_privacy: The member's avatar privacy, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.
        keep_proxy: Whether the member's proxy tags remain in the proxied message (``True``) or not
            (``False``). Default is ``False``.
        metadata_privacy: The member's metadata (eg. creation timestamp, message count, etc.)
            privacy. Must be either `~Privacy.PUBLIC` or `~Privacy.PRIVATE`. Default is public.
        proxy_tags: The member's proxy tags. Default is an empty set of proxy tags.
        visibility: The visibility privacy setting of the member, either `~Privacy.PUBLIC` or
            `~Privacy.PRIVATE`. Default is public.

    Attributes:
        id (str): The member's five-letter lowercase ID.
        name (str): The member's name.
        created (Timestamp): The member's creation date.
        name_privacy (Privacy): The member's name privacy.
        display_name (Optional[str]): The member's display name.
        description (Optional[str]): The member's description.
        description_privacy (Privacy): The member's description privacy.
        color (Optional[Color]): The member's color.
        birthday (Optional[Birthday]): The member's birthdate.
        birthday_privacy (Privacy): The member's birthday privacy.
        pronouns (Optional[str]): The member's pronouns.
        pronoun_privacy (Privacy): The member's pronouns privacy.
        avatar_url (Optional[str]): The member's avatar URL.
        avatar_privacy (Privacy): The member's avatar privacy.
        keep_proxy (bool): Whether the member's proxy tags remain in the proxied message (``True``)
            or not (``False``).
        metadata_privacy (Privacy): The member's metadata (eg. creation timestamp, message count,
            etc.) privacy.
        proxy_tags (ProxyTags): The member's proxy tags.
        visibility (Privacy): The visibility privacy setting of the member.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """

    def __init__(self, *,
        id: str,
        name: str,
        created: Union[None, Timestamp,datetime,str],
        name_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        display_name: Optional[str]=None,
        description: Optional[str]=None,
        description_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        color: Union[Color,str,None]=None,
        birthday: Union[Birthday,datetime,str,None]=None,
        birthday_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        pronouns: Optional[str]=None,
        pronoun_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        avatar_url: Optional[str]=None,
        avatar_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        keep_proxy: bool=False,
        metadata_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        proxy_tags: Optional[ProxyTags]=None,
        visibility: Union[Privacy,str]=Privacy.PUBLIC
    ):
        self.id = id
        self.name = name

        if created is not None:
            self.created = Timestamp.parse(created)
        else:
            self.created = None
        self.birthday = Birthday.parse(birthday)
        self.color = Color.parse(color)

        self.display_name = display_name
        self.description = description
        self.pronouns = pronouns
        self.avatar_url = avatar_url
        self.keep_proxy = keep_proxy

        if proxy_tags is None:
            self.proxy_tags = ProxyTags()
        else:
            self.proxy_tags = proxy_tags

        self.name_privacy = Privacy(name_privacy)
        self.description_privacy = Privacy(description_privacy)
        self.birthday_privacy = Privacy(birthday_privacy)
        self.pronoun_privacy = Privacy(pronoun_privacy)
        self.avatar_privacy = Privacy(avatar_privacy)
        self.metadata_privacy = Privacy(metadata_privacy)
        self.visibility = Privacy(visibility)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.id}')"

    def __str__(self):
        return self.id
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def _deep_equal(self, other, new_member=False) -> bool:
        if new_member is False:
            return self.__dict__ == other.__dict__
        elif new_member is True:
            def mutate_dict(dict):
                current_dict = dict.copy()
                keys_to_delete = ["id", "created"]
                privacy_keys = ["name_privacy", "description_privacy", 
                               "birthday_privacy", "avatar_privacy", "metadata_privacy", 
                               "pronoun_privacy"]
                for key in keys_to_delete:
                    del current_dict[key]
                for key in privacy_keys:
                    if current_dict[key] is None:
                        current_dict[key] = "public"
                    
            return mutate_dict(self.__dict__) == mutate_dict(other.__dict__)

    @staticmethod
    def from_json(member: Dict[str,Any]):
        """Static method to convert a member `dict` to a `Member` object.

        Args:
            member: Dictionary representing a system, e.g. one received directly from the API. Must
            have a value for the ``id`` and ``created`` attributes.

        Returns:
            Member: The corresponding `Member` object.
        """
        if not "proxy_tags" in member:
            proxy_tags = ProxyTags()
        else:
            proxy_tags = ProxyTags.from_json(member["proxy_tags"])
        return Member(
            id=member["id"],
            name=member["name"],
            name_privacy=member.get("name_privacy", "public"),
            created=member["created"],
            display_name=member.get("display_name"),
            description=member.get("description"),
            description_privacy=member.get("description_privacy", "public"),
            color=member.get("color"),
            birthday=member.get("birthday"),
            birthday_privacy=member.get("birthday_privacy", "public"),
            pronouns=member.get("pronouns", "public"),
            pronoun_privacy=member.get("pronoun_privacy", "public"),
            avatar_url=member.get("avatar_url"),
            avatar_privacy=member.get("avatar_privacy", "public"),
            keep_proxy=member.get("keep_proxy", False),
            metadata_privacy=member.get("metadata_privacy", "public"),
            proxy_tags=proxy_tags,
            visibility=member.get("visibility", "public"),
        )

    def json(self) -> Dict[str,Any]:
        """Generate the Python `dict` representing this member.
        """
        return {
            "id": self.id,
            "name": self.name,
            "name_privacy": self.name_privacy.value,
            "created": self.created.json(),
            "display_name": self.display_name,
            "description": self.description,
            "description_privacy": self.description_privacy.value,
            "color": self.color.json(),
            "birthday": self.birthday.json(),
            "birthday_privacy": self.birthday_privacy.value,
            "pronouns": self.pronouns,
            "pronoun_privacy": self.pronoun_privacy.value,
            "avatar_url": self.avatar_url,
            "avatar_privacy": self.avatar_privacy.value,
            "keep_proxy": self.keep_proxy,
            "metadata_privacy": self.metadata_privacy.value,
            "proxy_tags": self.proxy_tags.json(),
            "visibility": self.visibility.value,
        }

class Switch:
    """Represents a switch event.

    Args:
        timestamp: Timestamp of the switch. May be a string formatted as
            ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601 format), a
            `Timestamp`, or a `datetime`_.
        members: Members involved. May be a list of the five-letter member IDs as strings, or a
            list of `Member` models, though cannot be mixed.

    Attributes:
        timestamp (Timestamp): Timestamp of the switch.
        members (Union[Sequence[str],Sequence[Member]]): Members involved.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """
    def __init__(self, *,
        timestamp: Union[Timestamp,str],
        members: Union[Sequence[str],Sequence[Member]]
    ):
        self.timestamp = Timestamp.parse(timestamp)

        if members is None or len(members) == 0:
            self.members = []
        else:
            self.members = [member for member in members]

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.timestamp}>"
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_json(switch: Dict[str,str]):
        """Static method to convert a switch `dict` to a `Switch` object.

        Args:
            switch: Dictionary representing a switch, e.g. one received directly from the API. Must
            have a value for the ``members`` and ``timestamp`` attributes. See this class's
            initializer documentation for what format those are expected to be in.

        Returns:
            Switch: The corresponding `Switch` object.
        """
        return Switch(
            timestamp=switch["timestamp"],
            members=switch["members"]
        )

    def json(self) -> Dict[str,Any]:
        """Return Python `dict` representing this switch.
        """
        return {
            "timestamp": self.timestamp.json(),
            "members": self.members
        }

class Message:
    """Represents a proxied message.

    Args:
        timestamp: Timestamp of the message. May be a string for
            atted as ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601
            format), a `Timestamp`, or a `datetime`_.
        id: The ID of the Discord message sent by the webhook.
        original: The ID of the (presumably deleted) original Discord message sent by the account.
        sender: The user ID of the account that sent the message.
        channel: The ID of the channel the message was sent to.
        system: The system that proxied the message.
        member: The member that proxied the message.

    Attributes:
        timestamp (Timestamp): Timestamp of the message.
        id (int): The ID of the Discord message sent by the webhook.
        original (int): The ID of the (presumably deleted) original Discord message sent by the
            account.
        sender (int): The user ID of the account that sent the message.
        channel (int): The ID of the channel the message was sent to.
        system (System): The system that proxied the message.
        member (Member): The member that proxied the message.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """
    def __init__(self, *,
        timestamp: Union[Timestamp,datetime,str],
        id: Union[int,str],
        original: Union[int,str],
        sender: Union[int,str],
        channel: Union[int,str],
        system: System,
        member: Member
    ):
        self.id = int(id)
        self.original = int(original)
        self.sender = int(sender)
        self.channel = int(channel)
        self.system = system
        self.member = member

        self.timestamp = Timestamp.parse(timestamp)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_json(message: Dict[str,Any]):
        """Static method to convert a message `dict` to a `Message` object.

        Args:
            message: Dictionary representing a message, e.g. one received directly from the API.
            Must have a value the same attributes as required by the `Message` initializer.

        Returns:
            Message: The corresponding `Message` object.
        """
        return Message(
            timestamp=message["timestamp"],
            id=message["id"],
            original=message["original"],
            sender=message["sender"],
            channel=message["channel"],
            system=System.from_json(message["system"]),
            member=Member.from_json(message["member"])
        )

    def json(self) -> Dict[str,Any]:
        """Return Python `dict` representing this message.
        """
        return {
            "timestamp": self.timestamp.json(),
            "id": str(self.id),
            "original": str(self.original),
            "sender": str(self.sender),
            "channel": str(self.channel),
            "system": self.system.json(),
            "member": self.member.json()
        }


