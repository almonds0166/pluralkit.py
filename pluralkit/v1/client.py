
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)

import asyncio
import aiohttp
import json
import datetime

from .models import System, Member, Switch
from .errors import *
from .utils import *

class Client:
    """Represents a client that interacts with the PluralKit API.

    Args:
        token: The PluralKit authorization token, received by the ``pk;token`` command.
        user_agent: The UserAgent header to use with the API.

    Attributes:
        token: The client's PluralKit authorization token.
        user_agent: The UserAgent header used with the API.
    """

    SERVER = "https://api.pluralkit.me/v1"

    def __init__(self, token: Optional[str]=None, user_agent: Optional[str]=None):
        self.token = token
        self.headers = { }
        if token:
            self.headers["Authorization"] = token
        if user_agent:
            self.headers["UserAgent"] = user_agent
        self.content_headers = self.headers.copy()
        self.content_headers['Content-Type'] = "application/json"
        self._id = None

    @property
    def id(self) -> Optional[str]:
        """The five-letter lowercase PluralKit system ID of this client, if initialized.
        """
        return self._id

    async def _check_self_id(self):
        if self._id is None:
            system = await self.get_system()
            self._id = system.id
    
    @staticmethod
    def get_url(self, system):
        if system is None:
            if not self.token: raise AuthorizationError() # please pass in your token to the client
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

        return url



    async def get_system(self, system: Union[System,str,int,None]=None) -> System:
        """Return a system by its system ID or Discord user ID.

        Args:
            system: The system ID, Discord user ID, or System object of the system. If None, returns
                the system of the client.

        Returns:
            system (System): The desired system.
        """
        url = Client.get_url(self, system)


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

                system = System.from_json(resp)

                if url.endswith("/s"):
                    # remember self ID for the future
                    self._id = system.id

                return system

    async def get_members(self, system: Union[System,str,int,None]=None):
        """Retrieve list of a system's members.

        Args:
            system: The system ID, Discord user ID, or System object of the system. If None, returns
                a list of the client system's members.

        Yields:
            member (Member): The next system member.
        """

        if system is None:
            # get own system
            await self._check_self_id()
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
                    member = Member.from_json(item)

                    yield member

    async def edit_member(self, member_id: str, **kwargs) -> Member:
        """Edits a member of the system with the authorization token passed at initialization.

        Args:
            member_id: The ID of the member to be edited.
            **kwargs: Any number of keyworded patchable values from `PluralKit's member model`_.
        
        Keyword Args:
            name (str): New name of the member.
            display_name (Optional[str]): New display name of the member. If ``None`` is passed,
                this field is cleared.
            description (Optional[str]): New description of the member. If ``None`` is passed, this
                field is cleared.
            pronouns (Optional[str]): New pronouns of the member. If ``None`` is passed, this field
                is cleared.
            color (Union[str,None]): New color of the member. If a string, must be formatted
                as a 6-character hex string (e.g. "ff7000"), sans the # symbol. If ``None`` is
                passed, this field is cleared.
            avatar_url (Optional[str]): New avatar URL for the member. If ``None`` is passed, this
                field is cleared.
            birthday (Union[Timestamp,str]): New birthdate of the member. If a string, must be
                formatted as ``YYYY-MM-DD``. A year of ``0001`` or ``0004`` represents a hidden
                year. If ``None`` is passed, this field is cleared.
            proxy_tags (Union[ProxyTags,Sequence[ProxyTag],Sequence[Dict[str,str]]]): New proxy
                tags of the member. May be a ProxyTags object, a sequence of ProxyTag objects, or a
                sequence of Python dictionaries with the keys "prefix" and "suffix".
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message.
            visibility (Union[Privacy,str,None]): New visibility privacy for the member. Must be
                either Privacy.PUBLIC or Privacy.PRIVATE. If ``None`` is passed, this field is
                reset to public.
            name_privacy (Union[Privacy,str,None]): New name privacy for the member. Must be either
                Privacy.PUBLIC or Privacy.PRIVATE. If ``None`` is passed, this field is reset to
                public.
            description_privacy (Union[Privacy,str,None]): New description privacy for the member.
                Must be either Privacy.PUBLIC or Privacy.PRIVATE. If ``None`` is passed, this field
                is reset to public.
            avatar_privacy (Union[Privacy,str,None]): New avatar privacy for the member. Must be
                either Privacy.PUBLIC or Privacy.PRIVATE. If ``None`` is passed, this field is
                reset to public.
            pronoun_privacy (Union[Privacy,str]): New pronouns privacy for the member. Must be
                either Privacy.PUBLIC or Privacy.PRIVATE. If ``None`` is passed, this field is
                reset to public.
            metadata_privacy (Union[Privacy,str]): New metadata (eg. creation timestamp, message
                count, etc.) privacy for the member. Must be either Privacy.PUBLIC or
                Privacy.PRIVATE. If ``None`` is passed, this field is reset to public.

        Returns:
            member (Member): Modified member object.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        """

        if self.token is None:
            raise AuthorizationError()
        
        for key, value in kwargs.items():
            kwargs = await member_value(kwargs=kwargs, key=key, value=value)

        json_payload = json.dumps(kwargs, ensure_ascii=False)
        async with aiohttp.ClientSession(headers=self.content_headers) as session:
            async with session.patch(f"{self.SERVER}/m/{member_id}", data=json_payload, ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError
                elif response.status == 200:
                    item = await response.json()
                    return Member.from_json(item)
                else:
                    raise Exception(f"Something went wrong with your request. You received a {response.status} http code, here is a list of possible http codes")
    
    async def get_member(self, member_id: str) -> Member:
        """Gets a system member

        Args:
            member_id: The ID of the member to be fetched.
        
        Returns:
            member (Member): Member object.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.SERVER}/m/{member_id}", ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError()
                elif response.status == 200:
                    item = await response.json()
                    return Member.from_json(item)
                else:
                    raise Exception(f"Something went wrong with your request. You received a {response.status} http code, here is a list of possible http codes")

    async def new_member(self, **kwargs):
        """Creates a new member of the system with the authorization token passed at initialization.

        Args:
            name: Name of the new member
            **kwargs: Any number of keyworded patchable values from `PluralKit's member model`_.
        
        Keyword Args:
            display_name (Optional[str]): New display name of the member. Default is None.
            description (Optional[str]): New description of the member. Default is None.
            pronouns (Optional[str]): New pronouns of the member. Default is None.
            color (Union[str,None]): New color of the member. If a string, must be formatted
                as a 6-character hex string (e.g. "ff7000"), sans the # symbol. Default is None.
            avatar_url (Optional[str]): New avatar URL for the member. Default is None.
            birthday (Union[Timestamp,str]): New birthdate of the member. If a string, must be
                formatted as ``YYYY-MM-DD``. A year of ``0001`` or ``0004`` represents a hidden
                year. Default is None.
            proxy_tags (Union[ProxyTags,Sequence[ProxyTag],Sequence[Dict[str,str]]]): New proxy
                tags of the member. May be a ProxyTags object, a sequence of ProxyTag objects, or a
                sequence of Python dictionaries with the keys "prefix" and "suffix". Default is an
                empty set of proxy tags.
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message. Default is ``False``.
            visibility (Union[Privacy,str,None]): New visibility privacy for the member. Must be
                either Privacy.PUBLIC or Privacy.PRIVATE. Default is public.
            name_privacy (Union[Privacy,str,None]): New name privacy for the member. Must be either
                Privacy.PUBLIC or Privacy.PRIVATE. Default is public.
            description_privacy (Union[Privacy,str,None]): New description privacy for the member.
                Must be either Privacy.PUBLIC or Privacy.PRIVATE. Default is public.
            avatar_privacy (Union[Privacy,str,None]): New avatar privacy for the member. Must be
                either Privacy.PUBLIC or Privacy.PRIVATE. Default is public.
            pronoun_privacy (Union[Privacy,str]): New pronouns privacy for the member. Must be
                either Privacy.PUBLIC or Privacy.PRIVATE. Default is public.
            metadata_privacy (Union[Privacy,str]): New metadata (eg. creation timestamp, message
                count, etc.) privacy for the member. Must be either Privacy.PUBLIC or
                Privacy.PRIVATE. Default is public.

        Returns:
            member (Member): New member object.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        """
        #Finish editing this so it makes sense in the context it's in
        if self.token is None:
            raise AuthorizationError()
        self._name = None
        for key, value in kwargs.items():
            if key == "name":
                self._name = value
            kwargs = await member_value(kwargs=kwargs, key=key, value=value)
        if self._name is None:
            raise Exception("Must have field 'name'")

        json_payload = json.dumps(kwargs, ensure_ascii=False)
        async with aiohttp.ClientSession(headers=self.content_headers) as session:
            async with session.post(f"{self.SERVER}/m/", data=json_payload, ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError
                elif response.status == 200:
                    item = await response.json()
                    return Member.from_json(item)
                else:
                    raise Exception(f"Something went wrong with your request. You received a {response.status} http code, here is a list of possible http codes")

    async def get_switches(self, system=None):
        """Todo.
        """
        
        if system is None: raise Exception("Must have system ID, even with an authorization token")

        elif isinstance(system, System):
            # System object
            system_url = f"/s/{system.id}"
        elif isinstance(system, str):
            # system ID
            system_url = f"/s/{system}"

        url = f"https://api.pluralkit.me/v1{system_url}/switches"

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
                    switch = Switch.from_json(item)
                    yield switch

    async def new_switch(self, members: Sequence[str]):
        """Todo.
        """

        url = "https://api.pluralkit.me/v1/s/switches"
        payload = json.dumps({"members": members}, ensure_ascii=False)

        async with aiohttp.ClientSession(trace_configs=None, headers=self.content_headers) as session:
            async with session.post(url, data=payload, ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError()
                elif response.status == 403:
                    raise AccessForbidden()
                    
                if response.status != 204: # catch-all
                    raise PluralKitException()


