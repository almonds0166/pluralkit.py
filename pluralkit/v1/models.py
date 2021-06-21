from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)

import pytz
from colour import Color
from .errors import *

class Privacy(Enum):
    """Represents the two privacies accepted by PluralKit.
    """
    PUBLIC = "public"
    PRIVATE = "private"
    NULL = None # legacy, effectively resets privacy to "public"
    
class Timestamp(datetime):
    """Represents a PluralKit UTC timestamp.

    This class is initialized in the same way that a datetime object is.

    Hint:
        Use Timestamp.from_datetime to convert from a datetime object.
    """

    @staticmethod
    def from_datetime(dt: datetime):
        """Cast a datetime object to the corresponding Timestamp.

        Args:
            dt: The datetime object to cast. If timezone naive, it's assumed to be UTC.

        Returns:
            timestamp (Timestamp).
        """
        dt = dt.astimezone(pytz.UTC) # convert to UTC if timezone info is available.
        self.dt = Timestamp(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond
        )

    def to_iso(self) -> str:
        """Convert this timestamp to the ISO 8601 format that PluralKit uses internally.
        """
        return datetime.strptime(self, r"%Y-%m-%dT%H:%M:%S.%fZ")

    def to_birthday(self) -> str:
        """Convert this timestamp to the YYYY-MM-DD representation, suitable for birthdates.
        """
        return datetime.strptime(self, r"%Y-%m-%d")

class ProxyTag:
    """Represents a single PluralKit proxy tag.

    Args:
        prefix: Prefix that will enclose proxied messages.
        suffix: Suffix that will enclose proxied messages.

    Note:
        At least one of the ``suffix`` or ``prefix`` arguments must be passed.
    
    Attributes:
        prefix: Prefix that will enclose proxied messages.
        suffix: Suffix that will enclose proxied messages.
    """
    def __init__(self, *,
        prefix: Optional[str]=None,
        suffix: Optional[str]=None,
    ):
        assert prefix or suffix, \
            "A valid proxy tag must have at least one of the prefix or suffix defined."
        self.prefix = prefix
        self.suffix = suffix

    @staticmethod
    def from_dict(proxy_tag: Dict[str,str]):
        """Static method to convert a proxy tag Dict to a ProxyTag.

        Args:
            proxy_tag: Dictionary representing a proxy tag. Must have at least one of ``prefix`` or
                ``suffix`` as keys.

        Returns:
            proxy_tag (ProxyTag): The corresponding ProxyTag object.
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
            message: Message to parse. Should already be stripped of outer whitespace.
        """
        return (True if not self.prefix else message.startswith(self.prefix)) \
            and (True if not self.suffix else message.endswith(self.suffix))

    def json(self) -> Dict[str,str]:
        """Return the JSON object representing this proxy tag as a Python Dict.
        """
        return {
            "prefix": self.prefix,
            "suffix": self.suffix,
        }

class ProxyTags:
    """Represents a set of PluralKit proxy tags.

    Hint:
        ProxyTags objects can be iterated and indexed to yield its underlying ProxyTag objects.    
    
    Args:
        proxy_tags: A sequence of ProxyTag objects.
    """
    def __init__(self, proxy_tags: Optional[Sequence[ProxyTag]]=None):
        if proxy_tags is None: proxy_tags = tuple()
        self._proxy_tags = tuple(proxy_tags)

    def __repr__(self):
        return f"{self.__class__.__name__}<{len(self._proxy_tags)}>"

    def __iter__(self):
        for proxy_tag in self._proxy_tags:
            yield proxy_tag

    def __getitem__(self, index):
        return self._proxy_tags[index]

    @staticmethod
    def from_dict(proxy_tags: Sequence[Dict[str,str]]):
        """Static method to convert a list of proxy tags to a ProxyTags object.

        Args:
            proxy_tags: Sequence of Python dictionaries, each representing a proxy tag.

        Returns:
            proxy_tags (ProxyTags): The corresponding ProxyTags object.
        """
        return ProxyTags(ProxyTag.from_dict(proxy_tag) for proxy_tag in proxy_tags)

    def match(self, message: str) -> bool:
        """Determine if a given message would be proxied under this set of proxy tags.
        
        Args:
            message: Message to parse. Should already be stripped of outer whitespace.
        """
        return any(proxy_tag.match(message) for proxy_tag in self)

    def json(self) -> List[Dict[str,str]]:
        """Return the JSON object representing this proxy tag as a list of Python Dict.
        """
        return [proxy_tag.json() for proxy_tag in self]

class System:
    """Represents a PluralKit system.

    Args:
        id: The system's five-character lowercase ID.
        created: The system's creation date. May be a string formatted as
            ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601 format) or a
            Timestamp object.
        name: The name of the system. Default None.
        description: The description of the system. Default None.
        tag: The system's tag appended to display names. Default None.
        avatar_url: The system's avatar URL. Default None.
        tz: The system's tzdb timezone. May be a string or a pytz.timezone object. Default is UTC.
        description_privacy: The system's description privacy, either Privacy.PUBLIC or
            Privacy.PRIVATE. Default is public.
        member_list_privacy: The system's member list privacy, either Privacy.PUBLIC or
            Privacy.PRIVATE. Default is public.
        front_privacy: The system's fronting privacy, either Privacy.PUBLIC or Privacy.PRIVATE.
            Default is public.
        front_history_privacy: The system's fronting history privacy, either Privacy.PUBLIC or
            Privacy.PRIVATE. Default is public.

    Attributes:
        id (str): The system's five-character lowercase ID.
        name (str): The name of the system.
        description (str): The description of the system.
        tag (str): The system's tag appended to display names.
        avatar_url (str): The system's avatar URL.
        tz (pytz.timezone): The system's tzdb timezone.
        created (Timestamp): The system's timestamp at creation.
        description_privacy (Privacy): The system's description privacy.
        member_list_privacy (Privacy): The system's member list privacy.
        front_privacy (Privacy): The system's fronting privacy.
        front_history_privacy (Privacy): The system's fronting history privacy.
    """

    def __init__(self, *,
        id: str,
        created: Union[Timestamp,str],
        name: Optional[str]=None,
        description: Optional[str]=None,
        tag: Optional[str]=None,
        avatar_url: Optional[str]=None,
        tz: Union[pytz.timezone,str]="UTC",
        description_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        member_list_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        front_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        front_history_privacy: Union[Privacy,str]=Privacy.PUBLIC
    ):
        self.id = id

        if isinstance(created, str):
            self.created = Timestamp.strptime(created, r"%Y-%m-%dT%H:%M:%S.%fZ")
        elif isinstance(created, datetime):
            self.created = Timestamp.from_datetime(created)
        elif isinstance(created, Timestamp):
            self.created = created

        if isinstance(tz, str):
            self.tz = pytz.timezone(tz)
        elif isinstance(tz, pytz.timezone):
            self.tz = tz

        self.name = name
        self.description = description
        self.tag = tag
        self.avatar_url = avatar_url

        self.description_privacy = Privacy(description_privacy)
        self.member_list_privacy = Privacy(member_list_privacy)
        self.front_privacy = Privacy(front_privacy)
        self.front_history_privacy = Privacy(front_history_privacy)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __str__(self):
        return self.id

    @staticmethod
    def from_dict(system: Dict[str,Any]):
        """Static method to convert a system Dict to a System object.

        Args:
            system: Dictionary representing a system, e.g. one received directly from the API. Must
            have a value for the ``id`` and ``created`` attributes.

        Returns:
            system (System): The corresponding System object.
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
        """Return Python Dict representing this system.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tag": self.tag,
            "avatar_url": self.avatar_url,
            "tz": self.tz.zone,
            "created": self.created.to_iso(),
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
            Timestamp, or a datetime.
        name_privacy: The member's name privacy, either Privacy.PUBLIC or Privacy.PRIVATE. Default
            is public.
        display_name: The member's display name. Default is None.
        description: The member's description. Default is None.
        description_privacy: The member's description privacy, either Privacy.PUBLIC or
            Privacy.PRIVATE. Default is public.
        color: The member's color. Default is None.
        birthday: The member's birthdate. May be a string formatted as ``{year}-{month}-{day}``, a
            Timestamp, or a datetime. Default is None.
        birthday_privacy: The member's birthdate privacy, either Privacy.PUBLIC or Privacy.PRIVATE.
            Default is public.
        pronouns: The member's pronouns. Default is None.
        pronoun_privacy: The member's pronouns privacy, either Privacy.PUBLIC or Privacy.PRIVATE.
            Default is public.
        avatar_url: The member's avatar URL.
        avatar_privacy: The member's avatar privacy, either Privacy.PUBLIC or Privacy.PRIVATE.
            Default is public.
        keep_proxy: Whether the member's proxy tags remain in the proxied message (``True``) or not
            (``False``). Default is ``False``.
        metadata_privacy: The member's metadata (eg. creation timestamp, message count, etc.)
            privacy. Must be either Privacy.PUBLIC or Privacy.PRIVATE. Default is public.
        proxy_tags: The member's proxy tags. Default is an empty set of proxy tags.
        visibility: The visibility privacy setting of the member, either Privacy.PUBLIC or
            Privacy.PRIVATE. Default is public.

    Attributes:
        id (str): The member's five-letter lowercase ID.
        name (Optional[str]): The member's name.
        created (Timestamp): The member's creation date.
        name_privacy (Privacy): The member's name privacy.
        display_name (Optional[str]): The member's display name.
        description (Optional[str]): The member's description.
        description_privacy (Privacy): The member's description privacy.
        color (Optional[str]): The member's color.
        birthday (Timestamp): The member's birthdate.
        birthday_privacy (Privacy): The member's birthdate privacy.
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
    """

    def __init__(self, *,
        id: str,
        name: str,
        created: Union[Timestamp,str],
        name_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        display_name: Optional[str]=None,
        description: Optional[str]=None,
        description_privacy: Union[Privacy,str]=Privacy.PUBLIC,
        color: Optional[str]=None,
        birthday: Union[Timestamp,str,None]=None,
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

        if isinstance(created, str):
            self.created = Timestamp.strptime(created, r"%Y-%m-%dT%H:%M:%S.%fZ")
        elif isinstance(created, datetime):
            self.created = Timestamp.from_datetime(created)
        elif isinstance(created, Timestamp):
            self.created = created

        self.display_name = display_name
        self.description = description
        self.color = color

        if isinstance(birthday, str):
            self.birthday = Timestamp.strptime(birthday, r"%Y-%m-%d")
        elif isinstance(birthday, datetime):
            self.birthday = Timestamp.from_datetime(birthday)
        elif isinstance(birthday, Timestamp):
            self.birthday = birthday

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
        return f"{self.__class__.__name__}({self.id})"

    def __str__(self):
        return self.id

    @staticmethod
    def from_dict(member: Dict[str,Any]):
        """Static method to convert a member Dict to a Member object.

        Args:
            member: Dictionary representing a system, e.g. one received directly from the API. Must
            have a value for the ``id`` and ``created`` attributes.

        Returns:
            member (Member): The corresponding Member object.
        """
        if not "proxy_tags" in member:
            proxy_tags = ProxyTags()
        else:
            proxy_tags = ProxyTags.from_dict(member["proxy_tags"])
        return Member(
            id=member["id"],
            name=member.get("name"),
            name_privacy=member.get("name_privacy"),
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
        """Return Python Dict representing this member.
        """
        return {
            "id": self.id,
            "name": self.name,
            "name_privacy": self.name_privacy.value,
            "created": self.created.to_iso(),
            "display_name": self.display_name,
            "description": self.description,
            "description_privacy": self.description_privacy.value,
            "color": self.color,
            "birthday": self.birthday.to_birthday(),
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
        timestamp: Timestamp of the switch. May be a string for
            atted as ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601
            format), a Timestamp, or a datetime.
        members: Members involved. May be a list of the five-letter member IDs as strings, or a
            list of Member models, though cannot be mixed.

    Attributes:
        timestamp (str): ISO formatted timestamp of the switch.
        members (Union[Sequence[str],Sequence[Member]]): Members involved.
    """
    def __init__(self, *,
        timestamp: Union[Timestamp,str],
        members: Union[Sequence[str],Sequence[Member]]
    ):
        if isinstance(timestamp, str):
            self.timestamp = Timestamp.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")
        elif isinstance(timestamp, datetime):
            self.timestamp = Timestamp.from_datetime(timestamp)
        elif isinstance(timestamp, Timestamp):
            self.timestamp = timestamp

        if members is None or len(members) == 0:
            self.members = []
        else:
            self.members = [member for member in members]

    @staticmethod
    def from_dict(switch: Dict[str,str]):
        """Static method to convert a switch Dict to a Switch object.

        Args:
            switch: Dictionary representing a switch, e.g. one received directly from the API. Must
            have a value for the ``members`` and ``timestamp`` attributes. See this class's
            initializer documentation for what format those are expected to be in.

        Returns:
            switch (Switch): The corresponding Switch object.
        """
        return Switch(
            timestamp=switch["timestamp"],
            members=switch["members"]
        )

    def json(self) -> Dict[str,Any]:
        """Return Python Dict representing this switch.
        """
        return {
            "timestamp": self.timestamp.to_iso(),
            "members": self.members
        }

class Message:
    """Represents a proxied message.

    Args:
        timestamp: Timestamp of the message. May be a string for
            atted as ``{year}-{month}-{day}T{hour}:{minute}:{second}.{microsecond}Z`` (ISO 8601
            format), a Timestamp, or a datetime.
        id: The ID of the Discord message sent by the webhook.
        original: The ID of the (deleted) Discord message sent by the account.
        sender: The user ID of the account that sent the message.
        channel: The ID of the channel the message was sent to.
        system: The System that proxied the message.
        member: The Member that proxied the message.

    Attributes:
        timestamp (Timestamp): Timestamp of the message.
        id (int): The ID of the Discord message sent by the webhook.
        original (int): The ID of the (deleted) Discord message sent by the account.
        sender (int): The user ID of the account that sent the message.
        channel (int): The ID of the channel the message was sent to.
        system (System): The System that proxied the message.
        member (Member): The Member that proxied the message.
    """
    def __init__(self, *,
        timestamp: Union[Timestamp,str],
        id: Union[int,str],
        original: Union[int,str],
        sender: Union[int,str],
        channel: Union[int,str],
        system: System,
        member: Member
    ):
        if isinstance(timestamp, str):
            self.timestamp = Timestamp.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")
        elif isinstance(timestamp, datetime):
            self.timestamp = Timestamp.from_datetime(timestamp)
        elif isinstance(timestamp, Timestamp):
            self.timestamp = timestamp
        self.id = int(id)
        self.original = int(original)
        self.sender = int(sender)
        self.channel = int(channel)
        self.system = system
        self.member = member

    @staticmethod
    def from_dict(message: Dict[str,Any]):
        """Static method to convert a message Dict to a Message object.

        Args:
            message: Dictionary representing a switch, e.g. one received directly from the API.
            Must have a value the same attributes as required by the Message initializer.

        Returns:
            message (Message): The corresponding Message object.
        """
        return Message(
            timestamp=message["timestamp"],
            id=message["id"],
            original=message["original"],
            sender=message["sender"],
            channel=message["channel"],
            system=System.from_dict(message["system"]),
            member=Member.from_dict(message["member"])
        )

    def json(self) -> Dict[str,Any]:
        """Return Python Dict representing this Message.
        """
        return {
            "timestamp": self.timestamp.to_iso(),
            "id": str(self.id),
            "original": str(self.original),
            "sender": str(self.sender),
            "channel": str(self.channel),
            "system": self.system.json(),
            "member": self.member.json()
        }


