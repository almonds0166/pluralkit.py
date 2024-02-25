
from __future__ import annotations

from dataclasses import dataclass
from string import ascii_lowercase as ALPHABET
from enum import Enum
from datetime import datetime, timedelta, tzinfo
import re
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Generator,
)
import warnings

import pytz
import colour

from .errors import *

# Enums

class Privacy(Enum):
    """Represents the privacies accepted by PluralKit.

    In general, default privacies are public.
    """
    PUBLIC = "public"
    PRIVATE = "private"
    #UNKNOWN = None # legacy, effectively resets privacy to "public"

    def json(self): return self.value

class AutoproxyMode(Enum):
    """Represents the autproxy modes.
    """
    OFF = "off"
    FRONT = "front"
    LATCH = "latch"
    MEMBER = "member"

    def json(self): return self.value

def _to_json(value):
    """Robust method to deep convert Model objects
    """
    if hasattr(value, "json"):
        return value.json()
    
    if isinstance(value, (list, set, tuple)):
        return [_to_json(v) for v in value]
    
    if isinstance(value, (dict,)):
        return {k: _to_json(v) for k, v in value.items()}
    
    return value

# Base class for all models

class Model:
    """Base class for all models.
    """

    def json(self):
        """Return a JSON object representing this model.
        """
        model = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"): continue
            if v is None: continue
            model[k] = _to_json(v)

        return model

    def __init__(self, json, ignore_keys=None):
        """Simple way to convert from API JSON object to the superclass
        """
        if ignore_keys is None: ignore_keys = ()
        cls = self.__class__

        for key, value in json.items():
            if key in ignore_keys: continue
            if key not in cls.__annotations__ and key not in _KEY_TRANSFORMATIONS:
                msg = f"unexpected key {key!r} in JSON object for {cls.__name__!r} construction"
                warnings.warn(msg)

            # convert PluralKit API key names to pluralkit.py attribute names
            # and convert to proper Models if necessary
            if key in _VALUE_TRANSFORMATIONS:
                Constructor = _VALUE_TRANSFORMATIONS[key]
                value = Constructor(value) if value is not None else None
            key = _KEY_TRANSFORMATIONS.get(key, key)

            self.__dict__[key] = value

# IDs

class PluralKitId(Model):
    """Base class for PluralKit IDs.
    """
    uuid: Optional[str]
    id: Optional[str]

    __slots__ = ["uuid", "id"]

    def _check_id(self, id):
        return len(id) == 5 and all(c in ALPHABET for c in id)

    def _check_uuid(self, uuid):
        pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        result = re.match(pattern, uuid)
        return bool(result)

    def __init__(self, id=None, uuid=None):
        if uuid is None and id is None:
            raise ValueError(f"{self.CONTEXT} ID object must include at least one of: id, uuid")

        # accept any order/combination of inputs
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "uuid", None)
        if id is not None:
            if self._check_id(id):
                object.__setattr__(self, "id", id)
            elif self._check_uuid(id):
                object.__setattr__(self, "uuid", id)
            else:
                raise ValueError(f"Malformed id given: {id!r}")
        if uuid is not None:
            if self._check_uuid(uuid):
                object.__setattr__(self, "uuid", uuid)
            elif self._check_id(uuid):
                object.__setattr__(self, "id", uuid)
            else:
                raise ValueError(f"Malformed uuid given: {uuid!r}")

    def __setattr__(self, name, value):
        msg = f"cannot assign to field {name!r}"
        raise AttributeError(msg)

    def __str__(self):
        return f"{self.uuid}" if self.uuid is not None else f"{self.id}"

    def __repr__(self):
        attrs = f"{self.id!r}"
        if self.uuid is not None: attrs += f", {self.uuid!r}"
        return f"{self.__class__.__name__}({attrs})"

    json = __str__

class MemberId(PluralKitId):
    """Member IDs.
    """
    CONTEXT = "Member"

class SystemId(PluralKitId):
    """System IDs.
    """
    CONTEXT = "System"

class GroupId(PluralKitId):
    """Group IDs.
    """
    CONTEXT = "Group"

class SwitchId(PluralKitId):
    """Switch IDs.

    Switches don't have five-letter IDs, so this must be given the full switch UUID.
    """
    uuid: str
    CONTEXT = "Switch"
    __slots__ = ["uuid"]

    def __init__(self, uuid):
        if uuid is None:
            raise ValueError(f"{self.CONTEXT} ID object must include uuid")

        object.__setattr__(self, "uuid", uuid)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.uuid!r})"

# Primitives

class Color(colour.Color, Model):
    """Represents a color.

    This class is initialized in the same way that a `colour.Color`_ object is. It may also take a
    `colour.Color`_ object directly.
    
    .. _`colour.Color`: https://pypi.org/project/colour/#instantiation
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            arg = args[0]
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

    def __str__(self):
        return self.hex_l[1:]

    json = __str__

class Timestamp(Model):
    """Represents a PluralKit UTC timestamp.

    This class works by wrapping around a `datetime` object. Use ``ts.datetime`` to access it, for
    any `Timestamp` ``ts``.

    This class may be initialized in the same way that a `datetime` object is. It may also take a
    `datetime` object, a `Timestamp` object, or an ISO 8601 formatted string directly.
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
                try:
                    self.datetime = datetime.strptime(dt, r"%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    self.datetime = datetime.strptime(dt, r"%Y-%m-%dT%H:%M:%SZ")
            elif isinstance(dt, Timestamp):
                self.datetime = dt.datetime
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
        return f"{self.__class__.__name__}({self.json()!r})"

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

    This model inherits from `Timestamp`.
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
    """Member settings for a specific server.

    Attributes:
        display_name: The member's display name in the guild.
        avatar_url: The URL of the member's avatar image in the guild.
    """
    display_name: Optional[str]
    avatar_url: Optional[str]

class SystemGuildSettings(Model):
    """System settings for a specific server.

    Attributes:
        proxying_enabled: Whether proxying is enabled in the given server.
        tag: The system's tag (appended to the server username) for the given server.
        tag_enabled: Whether or not the system tag is shown in this server.
    """
    proxying_enabled: bool
    tag_enabled: bool
    tag: Optional[str]

class SystemSettings(Model):
    """Represents a system's settings.

    Attributes:
        timezone: The system's timezone.
        pings_enabled: Whether this system has pings enabled.
        latch_timeout: System's autoproxy latch timeout.
        member_default_private: Whether members created through the bot have privacy settings set
            to private by default.
        group_default_private: Whether groups created through the bot have privacy settings set to
            private by default.
        show_private_info: Whether the bot shows the system's own private information without
            requiring a ``-private`` flag.
        member_limit: System member limit, usually 1000.
        group_limit: System group limit, usually 250.
    """
    timezone: Timezone
    pings_enabled: bool
    latch_timeout: Optional[int]
    member_default_private: bool
    group_default_private: bool
    show_private_info: bool
    member_limit: int
    group_limit: int

    def __init__(self, json):
        Model.__init__(self, json, ("description_templates"))

class AutoproxySettings(Model):
    """Represents a system's autoproxy settings.

    Attributes:
        autoproxy_mode: The system's autoproxy mode.
        autoproxy_member: ID of current autoproxy member. (None if autoproxy mode is set to
            ``front``.)
        last_latch_timestamp: Timestamp of last message. (None if autoproxy mode isn't set to
            ``latch``.)
    """
    autoproxy_mode: AutoproxyMode
    autoproxy_member: Optional[MemberId]
    last_latch_timestamp: Optional[Timestamp]

# Proxy tags

class ProxyTag(Model):
    """Represents a single PluralKit proxy tag.

    Hint:
        A ProxyTag object can be called to see if it would match a message: ::

            >>> pt = ProxyTag("{", "}")
            >>> pt("This is an example.")
            False
            >>> pt("{This is another example.}")
            True

    Args:
        prefix: Prefix that will enclose proxied messages.
        suffix: Suffix that will enclose proxied messages.

    Keyword args:
        proxy_tag: Dictionary representing a proxy tag. Must have at least one of ``prefix`` or
            ``suffix`` as keys. The ``prefix`` and ``suffix`` args will overrule this dict.

    Important:
        At least one of the ``suffix`` or ``prefix`` arguments must be passed.
    
    Attributes:
        prefix (Optional[str]): Prefix that will enclose proxied messages.
        suffix (Optional[str]): Suffix that will enclose proxied messages.
    """
    def __init__(self,
        prefix: Optional[str]=None,
        suffix: Optional[str]=None,
        *,
        proxy_tag: Optional[Dict[str,str]]=None,
    ):

        if proxy_tag is not None:
            prefix = prefix or proxy_tag["prefix"]
            suffix = suffix or proxy_tag["suffix"]

        assert prefix or suffix, \
            "A valid proxy tag must have at least one of the prefix or suffix defined."
        self.prefix = prefix
        self.suffix = suffix
    
    def __eq__(self, other):
        return self.prefix == other.prefix and self.suffix == other.suffix
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        prefix = "" if not self.prefix else f"prefix={repr(self.prefix)}"
        suffix = "" if not self.suffix else f"suffix={repr(self.suffix)}"
        attrs = ", ".join(a for a in (prefix, suffix) if a)
        return (
            f"{self.__class__.__name__}({attrs})"
        )

    def __call__(self, message: str) -> bool:
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

class ProxyTags(Model):
    """Represents a set of PluralKit proxy tags.

    Hint:
        A ProxyTags object can be called to see if it would match a message: ::

            >>> pt_1 = ProxyTag("{", "}")
            >>> pt_2 = ProxyTag("A:")
            >>> pts = ProxyTags([pt_1, pt_2])
            >>> pts("{This is an example.}")
            True
            >>> pts("A: This is another example.")
            True

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
        return f"{self.__class__.__name__}({list(self._proxy_tags)!r})"

    def __iter__(self):
        for proxy_tag in self._proxy_tags:
            yield proxy_tag

    def __getitem__(self, index):
        return self._proxy_tags[index]
    
    def __eq__(self, other):
        return set(self._proxy_tags) == set(other._proxy_tags)
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __call__(self, message: str) -> bool:
        """Determine if a given message would be proxied under this set of proxy tags.
        
        Args:
            message: Message to parse.
        """
        return any(proxy_tag.match(message) for proxy_tag in self)

    def json(self) -> List[Dict[str,str]]:
        """Return the JSON object representing this proxy tag as a list of Python `dict`.
        """
        return [proxy_tag.json() for proxy_tag in self]

# Member, System, Group, Switch, and Message

class Member(Model):
    """Represents a PluralKit system member.

    Attributes:
        id: The member reference ID.
        system: The ID of the system this member belongs to.
        name: The member's name.
        created: The member's creation timestamp.
        display_name: The member's display name.
        description: The member's description.
        color: The member's color.
        birthday: The member's birthday.
        pronouns: The member's pronouns.
        avatar_url: The member's main avatar url that appears uncropped on the member card.
        webhook_avatar_url: The member's avatar url used for proxied messages instead of the main
            avatar.
        banner: The member's banner url.
        proxy_tags: The member's proxy tags.
        keep_proxy (bool): Whether the member's proxy tags remain in the proxied message or not.
        name_privacy: Whether the member name is visible to others or only the display name.
        description_privacy: Whether this member's description is visible to others.
        birthday_privacy: Whether the member's birthday is visible to others.
        pronoun_privacy: Whether the member's pronouns are visible to others.
        avatar_privacy: Whether the member's avatar is visible to others.
        metadata_privacy: Whether the member's metadata (i.e. creation timestamp, message count) is
            visible to others.
        visibility: Whether this member is visible to others (i.e. in member lists).
        autoproxy_enabled: Whether this member has autoproxy enabled. `None` if the member is not
            from the client's system.
        message_count: Member message count. `None` if the member's metadata privacy is set to
            private and the member is not from the client's system.
        last_message_timestamp: Timestamp of member's last message. `None` if the member's metadata
            privacy is set to private and the member is not from the client's system.
        tts: Whether this member has enabled tts or not
    """
    id: MemberId
    name: str
    created: Timestamp
    name_privacy: Optional[Privacy]
    description_privacy: Optional[Privacy]
    birthday_privacy: Optional[Privacy]
    pronoun_privacy: Optional[Privacy]
    avatar_privacy: Optional[Privacy]
    metadata_privacy: Optional[Privacy]
    visibility: Optional[Privacy]
    display_name: Optional[str]
    description: Optional[str]
    color: Optional[Color]
    birthday: Optional[Birthday]
    pronouns: Optional[str]
    avatar_url: Optional[str]
    webhook_avatar_url: Optional[str]
    keep_proxy: bool
    proxy_tags: Optional[ProxyTags]
    system: SystemId
    banner: Optional[str]
    autoproxy_enabled: Optional[bool]
    message_count: Optional[int]
    last_message_timestamp: Optional[Timestamp]
    tts: Optional[bool]

    def __str__(self):
        return f"{self.id!s}"
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, json):
        ignore_keys = ("uuid", "id", "privacy",)
        Model.__init__(self, json, ignore_keys)
        # fix up the remaining keys
        self.id = MemberId(id=json["id"], uuid=json["uuid"]) 
        # incorporate privacy keys when given
        if json.get("privacy") is not None:
            for key, value in json["privacy"].items():
                self.__dict__[key] = Privacy(value) if value is not None else None
        else:
            for key, _ in self.__class__.__annotations__.items():
                if "privacy" in key:
                    self.__dict__[key] = None # unknown         

class System(Model):
    """Represents a PluralKit system.

    Attributes:
        id: The system reference ID.
        name: The system's name.
        description: The system's description.
        created: The system's creation timestamp.
        tag: The system's tag appended to display names.
        pronouns: The system's pronouns.
        avatar_url: The system's avatar url.
        banner: The system's banner url.
        tz: The system's tzdb timezone.
        color: The system's color.
        description_privacy: Whether the system's description is visible to others.
        pronoun_privacy: Whether the system's pronouns are visible to others.
        member_list_privacy: Whether the system's member list is visible to others.
        group_list_privacy: Whether the system's group list is visible to others.
        front_privacy: Whether the system's current fronter information is visible to others.
        front_history_privacy: Whether the system's front history is visible to others.
    """
    id: SystemId
    created: Timestamp
    name: Optional[str]
    description: Optional[str]
    tag: Optional[str]
    avatar_url: Optional[str]
    tz: Timezone
    description_privacy: Optional[Privacy]
    pronoun_privacy: Optional[Privacy]
    member_list_privacy: Optional[Privacy]
    group_list_privacy: Optional[Privacy]
    front_privacy: Optional[Privacy]
    front_history_privacy: Optional[Privacy]
    pronouns: Optional[str]
    banner: Optional[str]
    color: Optional[Color]

    def __str__(self):
        return f"{self.id!s}"
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, json):
        ignore_keys = ("privacy", "webhook_url", "id", "uuid",)
        Model.__init__(self, json, ignore_keys)
        # fix up the remaining keys
        self.id = SystemId(id=json["id"], uuid=json["uuid"])
        # incorporate privacy keys when given
        if json.get("privacy") is not None:
            for key, value in json["privacy"].items():
                self.__dict__[key] = Privacy(value) if value is not None else None
        else:
            for key, _ in self.__class__.__annotations__.items():
                if "privacy" in key:
                    self.__dict__[key] = None # unknown

class Group(Model):
    """Represents a PluralKit system group.

    Attributes:
        id: The group reference ID.
        system: The ID of the system this group belongs to.
        name: Group name.
        display_name: Group display name.
        description: Group description.
        icon: Group icon url.
        banner: Group banner url.
        color: Group color.
        created: The group's creation timestamp.
        name_privacy: Whether the group name is visible to others or only the display name.
        description_privacy: Whether the group description is visilbe to others.
        icon_privacy: Whether the group icon is visible to others.
        list_privacy: Whether the group member list is visible to others.
        metadata_privacy: Whether the groups's metadata (i.e. created timestamp) is visible to
            others.
        visibility: Whether this group is visible to others (i.e. in group lists).
    """
    id: Optional[GroupId]
    system: SystemId
    name: str
    display_name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    banner: Optional[str]
    color: Optional[Color]
    name_privacy: Privacy
    description_privacy: Privacy
    icon_privacy: Privacy
    list_privacy: Privacy
    metadata_privacy: Privacy
    visibility: Privacy
    created: Timestamp

    def __str__(self):
        return f"{self.id!s}"
    
    def __eq__(self, other):
        return self.id == other.id

    def __init__(self, json):
        ignore_keys = ("uuid", "id", "privacy",)
        Model.__init__(self, json, ignore_keys)
        # fix up the remaining keys
        self.id = GroupId(id=json["id"], uuid=json["uuid"])
        for key, value in json["privacy"].items():
            self.__dict__[key] = Privacy(value)

class Switch(Model):
    """Represents a switch event.

    Note:
        ``members`` can either be a list of `Member` models or a list of `MemberId` objects,
        depending on the client method used.

        In particular, switch models from `Client.get_switches` carry `MemberId` objects, whereas
        switch models from  `~Client.get_switch`, `~Client.new_switch`, and `~Client.update_switch`
        carry full `Member` objects.

    Attributes:
        id: Switch's unique universal identifier (uuid).
        timestamp: Timestamp of the switch.
        members: Members involved.
    """
    id: SwitchId
    timestamp: Timestamp
    members: Union[Sequence[Member],Sequence[MemberId]]

    def __init__(self, json):
        ignore_keys = ("id", "members",) # "members" key is tricky
        Model.__init__(self, json, ignore_keys)
        # ...
        self.id = SwitchId(json["id"])
        if all(isinstance(m, str) for m in json["members"]):
            self.members = [MemberId(m) for m in json["members"]]
        else:
            self.members = [Member(m) for m in json["members"]]
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        return not self.__eq__(other)

class Message(Model):
    """Represents a proxied message.

    Attributes:
        timestamp: Timestamp of the message.
        id: The ID of the Discord message sent by the webhook.
        original: The ID of the (presumably deleted) original Discord message sent by the account.
        sender: The user ID of the account that sent the message.
        channel: The ID of the channel the message was sent to.
        guild: The ID of the guild the message was sent in.
        system: The system that proxied the message. ``None`` if system was deleted.
        member: The member that proxied the message. ``None`` if member was deleted.
    """
    timestamp: Timestamp
    id: int
    original: int
    sender: int
    channel: int
    guild: int
    system: Optional[System]
    member: Optional[Member]
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, json):
        ignore_keys = ("id", "system", "member",)
        Model.__init__(self, json, ignore_keys)
        # fix the remaining keys
        self.system = None if json["system"] is None else System(json["system"])
        self.member = None if json["member"] is None else Member(json["member"])
        self.id = int(json["id"])

def _proxy_tags_processor(proxy_tags):
    if not proxy_tags: return proxy_tags
    return ProxyTags([ProxyTag(proxy_tag=pt) for pt in proxy_tags])

# the following maps direct how to change the JSON objects as given by the API
# to make them ready for use (e.g. Python-friendly)
# see Model.__init__ for how this is used

# [name given by API] -> [new pk.py (Python-friendly) name]
_KEY_TRANSFORMATIONS = {
    # (So far, all key names in the API are Python-friendly)
}

# [name given by API] -> [constructor to use on this object]
_VALUE_TRANSFORMATIONS = {
    "system": SystemId, # can also be full system object (for Message)
    "color": lambda c: None if c is None else Color(c),
    "proxy_tags": _proxy_tags_processor,
    "created": Timestamp,
    "timestamp": Timestamp,
    "last_message_timestamp": Timestamp,
    "message_count": int,
    "channel": int,
    "original": int,
    "sender": int,
    "guild": int,
    "timezone": Timezone,
}

# Patchable keys, along with their respective checks
# These methods are for the client's patch (update) methods

def _max_string_length(context, max_len, null_allowed=True):
    def check(value):
        if null_allowed and value is None: return None
        if isinstance(value, str) and len(value) <= max_len: return value
        msg = (
            f"value for {context!r} must be shorter than {max_len} characters "
            f"(counted {len(value)})"
        )
        raise ValueError(msg)
    return check

def _check_color(c):
    if isinstance(c, Color): return c.json()
    c = Color(c) # will throw error if malformed
    return c.json()

def _check_privacy(p):
    if p is None: return None # null allowed
    if isinstance(p, Privacy): return p.value
    p = Privacy(p) # will throw error if malformed
    return p.value

def _check_timestamp(t):
    if isinstance(t, Timestamp): return t.json()
    t = Timestamp(t) # will throw error if malformed
    return t.json()

def _check_birthday(b):
    if b is None: return None # null allowed
    if isinstance(b, Birthday): return b.json()
    if isinstance(b, Timestamp): return Birthday(b).json()
    b = Birthday(b) # will throw error if malformed
    return b.json()

def _check_timezone(tz):
    if tz is None: return "UTC"
    if isinstance(tz, Timezone): return tz.json()
    tz = Timezone(tz) # will throw error if malformed
    return tz.json()

def _check_proxy_tags(pts):
    """Allowed: ProxyTag, ProxyTags, Sequence[ProxyTag]
    """
    if isinstance(pts, ProxyTags): return pts.json()
    if isinstance(pts, ProxyTag): return [pts.json()],
    try:
        json = []
        for pt in pts:
            if not isinstance(pt, ProxyTag):
                pt = ProxyTag(proxy_tag=pt)
            json.append(pt.json())
        return json
    except (TypeError, ValueError):
        msg = (
            f"Could not cast {pts!r} to ProxyTags. "
            f"Please pass in a ProxyTags object, a ProxyTag object, or an "
            f"iterable of ProxyTag objects."
        )
        raise ValueError(msg)

def _check_members(members):
    """For `Client.update_switch`
    """
    # special case for one member
    if isinstance(members, MemberId): return [str(members)]
    if isinstance(members, Member): return [str(members.id)]
    # otherwise
    try:
        json = []
        for m in members:
            if isinstance(m, Member):
                json.append(str(m.id))
            elif isinstance(m, MemberId):
                json.append(str(m))
            else:
                m = MemberId(m)
                json.append(str(m))
        return json
    except (TypeError, ValueError):
        msg = (
            f"Could not cast {members!r} to a list of MemberId or Member. "
            f"Please pass in a list of MemberId or Member objects."
        )
        raise ValueError(msg)

def _check_optional_member(m):
    """For `Client.update_autoproxy_settings`
    """
    if m is None: return None
    if isinstance(m, MemberId): return str(m)
    if isinstance(m, Member): return str(m.id)
    # otherwise
    try:
        if isinstance(m, Member):
            return str(m.id)
        elif isinstance(m, MemberId):
            return str(m)
        else:
            m = MemberId(m)
            return str(m)
    except (TypeError, ValueError):
        msg = (
            f"Could not cast {m!r} to a MemberId or Member. "
            f"Please pass in a MemberId or Member object."
        )
        raise ValueError(msg)


_PATCHABLE_SYSTEM_KEYS = {
    "name": _max_string_length("name", 100, null_allowed=False),
    "description": _max_string_length("description", 1000),
    "tag": _max_string_length("tag", 79),
    "pronouns": _max_string_length("pronouns", 100),
    # API will report whether any urls are publically (in)accessible
    "avatar_url": _max_string_length("avatar_url", 256),
    "banner": _max_string_length("banner", 256),
    "color": _check_color,
    "description_privacy": _check_privacy,
    "pronoun_privacy": _check_privacy,
    "member_list_privacy": _check_privacy,
    "group_list_privacy": _check_privacy,
    "front_privacy": _check_privacy,
    "front_history_privacy": _check_privacy,
}

_PATCHABLE_MEMBER_KEYS = {
    "name": _max_string_length("name", 100, null_allowed=False),
    "display_name": _max_string_length("display_name", 100),
    "color": _check_color,
    "birthday": _check_birthday,
    "pronouns": _max_string_length("pronouns", 100),
    "avatar_url": _max_string_length("avatar_url", 256),
    "banner": _max_string_length("banner", 256),
    "description": _max_string_length("description", 1000),
    "proxy_tags": _check_proxy_tags,
    "keep_proxy": bool,
    "visibility": _check_privacy,
    "name_privacy": _check_privacy,
    "description_privacy": _check_privacy,
    "birthday_privacy": _check_privacy,
    "pronoun_privacy": _check_privacy,
    "avatar_privacy": _check_privacy,
    "metadata_privacy": _check_privacy,
}

_PATCHABLE_GROUP_KEYS = {
    "name": _max_string_length("name", 100, null_allowed=False),
    "display_name": _max_string_length("display_name", 100),
    "description": _max_string_length("description", 1000),
    "icon": _max_string_length("icon", 256),
    "banner": _max_string_length("banner", 256),
    "color": _check_color,
    "name_privacy": _check_privacy,
    "description_privacy": _check_privacy,
    "icon_privacy": _check_privacy,
    "list_privacy": _check_privacy,
    "metadata_privacy": _check_privacy,
    "visibility": _check_privacy,
}

_PATCHABLE_SWITCH_KEYS = {
    "members": _check_members,
    "timestamp": _check_timestamp,
}

_PATCHABLE_AUTOPROXY_SETTINGS_KEYS = {
    "autoproxy_member": _check_optional_member,
}

_PATCHABLE_SYSTEM_SETTINGS_KEYS = {
    "timezone": _check_timezone,
    "pings_enabled": bool,
    "latch_timeout": lambda n: None if n is None else int(n), # time in seconds
    "member_default_private": bool,
    "group_default_private": bool,
    "show_private_info": bool,
}

_PATCHABLE_SYSTEM_GUILD_SETTINGS_KEYS = { # requires guild id
    "proxying_enabled": bool,
    "tag": _max_string_length("tag", 79),
    "tag_enabled": bool,
}

_PATCHABLE_MEMBER_GUILD_SETTINGS_KEYS = { # requires guild id
    "display_name": _max_string_length("display_name", 100),
    "avatar_url": _max_string_length("avatar_url", 256),
}

_PRIVACY_ASSOCIATED_KEYS = set((
    "visibility",
    "name_privacy",
    "description_privacy",
    "birthday_privacy",
    "pronoun_privacy",
    "avatar_privacy",
    "metadata_privacy",
    "member_list_privacy",
    "group_list_privacy",
    "front_privacy",
    "front_history_privacy",
    "icon_privacy",
    "list_privacy",
))
