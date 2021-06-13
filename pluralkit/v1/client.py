
from typing import (
   Any,
   Union, Optional,
   Tuple, List, Set, Sequence, Dict,
   AsyncIterable,
)

import asyncio
import aiohttp

from .models import System, Member, ProxyTag, ProxyTags
from .errors import *

class Client:
   """Represents a client that interacts with the PluralKit API.

   Args:
      token: The PluralKit authorization token, received by the ``pk;token`` command.
      user_agent: The UserAgent header to use with the API.
   """

   SERVER = "https://api.pluralkit.me/v1"

   def __init__(self, token: str, user_agent: Optional[str]=None):
      self.token = token
      self.headers = {
         "Authorization": token,
      }
      if user_agent:
         self.headers["UserAgent"] = user_agent

      self._ready = False
      self._id = None

   @property
   def ready(self) -> bool:
      """Whether the client has initialized its ``id`` propery yet.
      """
      return self._ready

   @property
   def id(self) -> Optional[str]:
      """The five-letter lowercase PluralKit system ID of this client, if initialized.
      """
      return self._id

   async def _check_ready(self):
      if not self._ready:
         system = await self.get_system()
         self._id = system.id
         self._ready = True

   async def get_system(self, system: Union[System,str,int,None]=None):
      """Return a system by its system ID or Discord user ID.

      Args:
         system: The system ID, Discord user ID, or System object of the system. If None, returns
            the system of the client.
      """
      #await self._check_ready()

      if system is None:
         # get own system
         url = f"{self.SERVER}/s"
      elif isinstance(system, System):
         # System object
         url = f"{self.SERVER}/s/{system.id}"
      elif isinstance(system, str):
         # system ID
         url = f"{self.SERVER}/s/{system}"
      elif isinstance(system, int):
         # Discord user ID
         url = f"{self.SERVER}/a/{system}"

      async with aiohttp.ClientSession(trace_configs=None, headers=self.headers) as session:
         async with session.get(url, ssl=True) as response:
            if response.status == 401:
               raise AuthorizationError()
            elif response.status == 404:
               if isinstance(system, str):
                  raise SystemNotFound(system)
               elif isinstance(system, int):
                  raise DiscordUserNotFound(system)
            
            if response.status != 200: # catch-all
               raise PluralKitException()

            resp = await response.json()

            system = System(
               id=resp["id"],
               name=resp["name"],
               description=resp["description"],
               tag=resp["tag"],
               avatar_url=resp["avatar_url"],
               tz=resp["tz"],
               created=resp["created"],
               description_privacy=resp["description_privacy"],
               member_list_privacy=resp["member_list_privacy"],
               front_privacy=resp["front_privacy"],
               front_history_privacy=resp["front_history_privacy"]
            )

            return system

   async def get_members(self, system: Union[System,str,int,None]=None):
      """Retrieve list of a system's members.

      Args:
         system: The system ID, Discord user ID, or System object of the system. If None, returns
            a list of the client system's members.
      """
      await self._check_ready()

      if system is None:
         # get own system
         url = f"{self.SERVER}/s/{self.id}/members"
      elif isinstance(system, System):
         # System object
         url = f"{self.SERVER}/s/{system.id}/members"
      elif isinstance(system, str):
         # system ID
         url = f"{self.SERVER}/s/{system}/members"
      elif isinstance(system, int):
         # Discord user ID
         system = await self.get_system(system)
         url = f"{self.SERVER}/s/{system.id}/members"

      async with aiohttp.ClientSession(trace_configs=None, headers=self.headers) as session:
         async with session.get(url, ssl=True) as response:
            if response.status == 401:
               raise AuthorizationError()
            elif response.status == 403:
               raise AccessForbidden()
            elif response.status == 404:
               if isinstance(system, str):
                  raise SystemNotFound(system)
               elif isinstance(system, int):
                  raise DiscordUserNotFound(system)
            
            if response.status != 200: # catch-all
               raise PluralKitException()

            resp = await response.json()

            for item in resp:
               member = Member(
                  id=item["id"],
                  name=item["name"],
                  name_privacy=item["name_privacy"],
                  created=item["created"],
                  display_name=item["display_name"],
                  description=item["description"],
                  description_privacy=item["description_privacy"],
                  color=item["color"],
                  birthday=item["birthday"],
                  birthday_privacy=item["birthday_privacy"],
                  pronouns=item["pronouns"],
                  pronoun_privacy=item["pronoun_privacy"],
                  avatar_url=item["avatar_url"],
                  avatar_privacy=item["avatar_privacy"],
                  keep_proxy=item["keep_proxy"],
                  metadata_privacy=item["metadata_privacy"],
                  proxy_tags=ProxyTags.from_dict(item["proxy_tags"]),
                  visibility=item["visibility"],
               )

               yield member

   #async def edit_system(self, system: Union[System,str,int,None], ...) -> System:
   #   ... # not yet implemented