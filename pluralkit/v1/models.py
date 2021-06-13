
from datetime import datetime, timedelta
from typing import (
   Any,
   Union, Optional,
   Tuple, List, Set, Sequence, Dict,
)

from pytz import timezone

class ProxyTag:
   """Represents a single PluralKit proxy tag.
   
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
      """
      return ProxyTag(
         prefix=proxy_tag["prefix"],
         suffix=proxy_tag["suffix"]
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
         "preifx": self.prefix,
         "suffix": self.suffix,
      }

class ProxyTags:
   """Represents a set of PluralKit proxy tags.
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
      """
      return ProxyTags(ProxyTag.from_dict(proxy_tag) for proxy_tag in proxy_tags)

   def match(self, message: str) -> bool:
      """Determine if a given message would be proxied under this set of proxy tags.

      Args
         message: Message to parse. Should already be stripped of outer whitespace.
      """
      return any(proxy_tag.match(message) for proxy_tag in self)

   def json(self) -> List[Dict[str,str]]:
      """Return the JSON object representing this proxy tag as a list of Python Dict.
      """
      return [proxy_tag.json() for proxy_tag in self]

class System:
   """Represents a PluralKit system.

   Attributes:
      id: The system's five-character lowercase ID.
   """

   def __init__(self, *,
      id: str,
      name: Optional[str]=None,
      description: Optional[str]=None,
      tag: Optional[str]=None,
      avatar_url: Optional[str]=None,
      tz: Union[timezone,str]="UTC",
      created: Union[datetime,str,None]=None,
      description_privacy: str="public",
      member_list_privacy: str="public",
      front_privacy: str="public",
      front_history_privacy: str="public"
   ):
      self.id = id
      if created is None:
         self._created = datetime.utcnow()
      elif isinstance(created, str):
         self._created = datetime.strptime(created, r"%Y-%m-%dT%H:%M:%S.%fZ") # expected ISO 8601
      elif isinstance(created, datetime):
         self._created = datetime
      if isinstance(tz, str):
         self._tz = timezone(tz) # expected tzdb identifier
      elif isinstance(tz, timezone):
         self._tz = tz
      self.name = name
      self.description = description
      self.tag = tag
      self.avatar_url = avatar_url
      self.description_privacy = description_privacy
      self.member_list_privacy = member_list_privacy
      self.front_privacy = front_privacy
      self.front_history_privacy = front_history_privacy

   def __repr__(self):
      return f"{self.__class__.__name__}({self.id})"

   def __str__(self):
      return self.id

   @property
   def created(self) -> str:
      """System creation time, UTC.
      """
      return self._created.strftime(r"%Y-%m-%dT%H:%M:%S.%fZ")
   
   @property
   def tz(self) -> str:
      """System time zone.
      """
      return self._tz.zone

   def json(self) -> Dict[str,Any]:
      """Return Python Dict representing this system.
      """
      return {
         "id": self.id,
         "name": self.name,
         "description": self.description,
         "tag": self.tag,
         "avatar_url": self.avatar_url,
         "tz": self.tz,
         "created": self.created,
         "description_privacy": self.description_privacy,
         "member_list_privacy": self.member_list_privacy,
         "front_privacy": self.front_privacy,
         "front_history_privacy": self.front_history_privacy
      }
   
class Member:
   """Represents a PluralKit system member.

   Attributes:
      id: The member's five-character lowercase ID.
      name: The member's name.
   """

   def __init__(self, *,
      id: str,
      name: str,
      name_privacy: str="public",
      created: Union[datetime,str,None]=None,
      display_name: Optional[str]=None,
      description: Optional[str]=None,
      description_privacy: str="public",
      color: Optional[str]=None,
      birthday: Optional[str]=None,
      birthday_privacy: str="public",
      pronouns: Optional[str]=None,
      pronoun_privacy: str="public",
      avatar_url: Optional[str]=None,
      avatar_privacy: str="public",
      keep_proxy: bool=False,
      metadata_privacy: str="public",
      proxy_tags: Optional[ProxyTags]=None,
      visibility: str="public"
   ):
      self.id = id
      self.name = name
      self.name_privacy = name_privacy
      if created is None:
         self._created = datetime.utcnow()
      elif isinstance(created, str):
         self._created = datetime.strptime(created, r"%Y-%m-%dT%H:%M:%S.%fZ") # expected ISO 8601
      elif isinstance(created, datetime):
         self._created = datetime
      self.display_name = display_name
      self.description = description
      self.description_privacy = description_privacy
      self.color = color
      self.birthday = birthday
      self.birthday_privacy = birthday_privacy
      self.pronouns = pronouns
      self.pronoun_privacy = pronoun_privacy
      self.avatar_url = avatar_url
      self.avatar_privacy = avatar_privacy
      self.keep_proxy = keep_proxy
      self.metadata_privacy = metadata_privacy
      if proxy_tags is None:
         self.proxy_tags = ProxyTags()
      else:
         self.proxy_tags = proxy_tags
      self.visibility = visibility

   def __repr__(self):
      return f"{self.__class__.__name__}({self.id})"

   def __str__(self):
      return self.id

   @property
   def created(self) -> str:
      """Member creation time, UTC.
      """
      return self._created.strftime(r"%Y-%m-%dT%H:%M:%S.%fZ")

   def json(self) -> Dict[str,Any]:
      """Return Python Dict representing this member.
      """
      return {
         "id": self.id,
         "name": self.name,
         "name_privacy": self.name_privacy,
         "created": self.created,
         "display_name": self.display_name,
         "description": self.description,
         "description_privacy": self.description_privacy,
         "color": self.color,
         "birthday": self.birthday,
         "birthday_privacy": self.birthday_privacy,
         "pronouns": self.pronouns,
         "pronoun_privacy": self.pronoun_privacy,
         "avatar_url": self.avatar_url,
         "avatar_privacy": self.avatar_privacy,
         "keep_proxy": self.keep_proxy,
         "metadata_privacy": self.metadata_privacy,
         "proxy_tags": self.proxy_tags.json(),
         "visibility": self.visibility,
      }

class Switch:
   """Represents a switch event.

   Args:
      timestamp: Timestamp of the switch.
      members: Members involved. May be a string of the five-letter member ID, or full Member
         models, though cannot be mixed.
   """
   def __init__(self, *,
      timestamp: Union[datetime,str,None]=None,
      members: Union[Sequence[str],Sequence[Member],None]=None
   ):
      if timestamp is None:
         self._timestamp = datetime.utcnow()
      elif isinstance(timestamp, str):
         self._timestamp = datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")
      elif isinstance(timestamp, datetime):
         self._timestamp = datetime
      if members is None or len(members) == 0:
         self.members = []
      else:
         self.members = [member for member in members]

   @property
   def timestamp(self) -> str:
      """Timestamp of switch, UTC.
      """
      return self._timestamp.strftime(r"%Y-%m-%dT%H:%M:%S.%fZ")

   def json(self) -> Dict[str,Any]:
      """Return Python Dict representing this switch.
      """
      return {
         "timestamp": self.timestamp,
         "members": self.members
      }

class Message:
   """Represents a proxied message.

   Args:
      timestamp: Timestamp of the message.
      id: The ID of the Discord message sent by the webhook.
      original: The ID of the (deleted) Discord message sent by the account.
      sender: The user ID of the account that sent the message.
      channel: The ID of the channel the message was sent to.
      system: The System that proxied the message.
      member: The Member that proxied the message.
   """
   def __init__(self, *,
      timestamp: Union[datetime,str],
      id: Union[int,str],
      original: Union[int,str],
      sender: Union[int,str],
      channel: Union[int,str],
      system: System,
      member: Member
   ):
      if timestamp is None:
         self._timestamp = datetime.utcnow()
      elif isinstance(timestamp, str):
         self._timestamp = datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")
      elif isinstance(timestamp, datetime):
         self._timestamp = datetime
      self.id = int(id)
      self.original = int(original)
      self.sender = int(sender)
      self.channel = int(channel)
      self.system = int(system)
      self.member = int(member)

   #@staticmethod
   #def from_id(id):
   #   pass
