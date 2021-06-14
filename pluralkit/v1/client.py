
from typing import (
   Any,
   Union, Optional,
   Tuple, List, Set, Sequence, Dict,
   AsyncIterable,
)

import asyncio
import aiohttp
import json
import datetime

from .models import System, Member, ProxyTag, ProxyTags, Colour
from .errors import *
from .utils import Utils as U

class Client:
    """Represents a client that interacts with the PluralKit API.

    Args:
        token: The PluralKit authorization token, received by the ``pk;token`` command.
        user_agent: The UserAgent header to use with the API.
    """

    SERVER = "https://api.pluralkit.me/v1"

    def __init__(self, token: str=None, user_agent: Optional[str]=None):
        self.token = token
        self.headers = { }
        if token:
            self.headers["Authorization"] = token
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

                system = U.pack_system(resp)

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
                        member = U.pack_member(item)

                        yield member

    async def edit_member(self, member_id: str, **kwargs) -> Member:
        """ Edits the a member of the system with the authorization token passed at initialization.
        Args:
            member_id: The id of the member to be edited
            Any number of keyworded patchable values from PK's member model: https://pluralkit.me/api/#member-model
        Returns:
            Modified member object.
        """

        if not self.token:
            raise AuthorizationError()
            
        for key, value in kwargs.items():
            kwargs = await U.member_value(kwargs=kwargs, key=key, value=value)
        

        content_headers = self.headers.copy()
        content_headers['Content-Type'] = "application/json"
        json_payload = json.dumps(kwargs, indent=4, ensure_ascii=False)
        async with aiohttp.ClientSession(headers=content_headers) as session:
            async with session.patch(f"{self.SERVER}/m/{member_id}", data=json_payload, ssl=True) as response:
                if response.status != 200:
                    raise PluralKitException()
                else:
                    item = await response.json()
                    return U.pack_member(item)
