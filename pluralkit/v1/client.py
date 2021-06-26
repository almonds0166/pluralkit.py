
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)

import asyncio
import aiohttp
import json
import datetime

from .models import Message, System, Member, Switch, Timestamp
from .errors import *
from .utils import *

class Client:
    """Represents a client that interacts with the PluralKit API.

    Args:
        token: The PluralKit authorization token, received by the ``pk;token`` command.
        user_agent: The User-Agent header to use with the API.

    Attributes:
        token (Optional[str]): The client's PluralKit authorization token.
        user_agent (Optional[str]): The User-Agent header used with the API.
    """

    SERVER = "https://api.pluralkit.me/v1"

    def __init__(self, token: Optional[str]=None, user_agent: Optional[str]=None):
        self.token = token
        self.headers = { }
        if token:
            self.headers["Authorization"] = token
        if user_agent:
            self.headers["User-Agent"] = user_agent
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
    def _get_system_url(self, system):
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
            system: The system ID (as `str`), Discord user ID (as `int`), or `~v1.models.System`
                object of the system. If ``None``, returns the system of the client.

        Returns:
            System: The retrieved system.
        """
        url = Client._get_system_url(self, system)


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
    
    async def edit_system(self, **kwargs):
        """"Todo.
        """

        if self.token is None:
            raise AuthorizationError()

        await self._check_self_id()
        url = f"https://api.pluralkit.me/v1/s/{self.id}"
    
        for key, value in kwargs.items():
            kwargs = await system_value(kwargs=kwargs, key=key, value=value)
        
        json_object = json.dumps(kwargs, ensure_ascii=False)

        async with aiohttp.ClientSession(trace_configs=None, headers=self.content_headers) as session:
            async with session.patch(url, data=json_object, ssl=True) as response:
                if response.status != 200: # catch-all
                    raise PluralKitException()

                resp = await response.json()

                system = System.from_json(resp)

                return system

    async def get_fronters(self, system: str=None):
        """Todo.
        """
        
        if system is None: 
            await self._check_self_id()
            url = f"{self.SERVER}/s/{self.id}/fronters"
        elif isinstance(system, str):
            url = f"{self.SERVER}/s/{system}/fronters"
        elif isinstance(system, System):
            url = f"{self.SERVER}/s/{system.id}/fronters"
        
        async with aiohttp.ClientSession(trace_configs=None, headers=self.headers) as session:
            async with session.get(url, ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError()
                elif response.status == 403:
                    raise AccessForbidden()
                if response.status != 200: # catch-all
                    raise PluralKitException()
                else:
                    resp = await response.json()
                    member_list = []
                    for fronter in resp['members']:
                        member_list.append(Member.from_json(fronter))
                    timestamp = Timestamp.from_json(resp['timestamp'])
                    return (timestamp, member_list)

    async def get_members(self, system: Union[System,str,int,None]=None):
        """Retrieve list of a system's members.

        Args:
            system: The system ID, Discord user ID, or System object of the system. If ``None``,
                returns a list of the client system's members.

        Yields:
            Member: The next system member.
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
    
    async def get_member(self, member_id: str) -> Member:
        """Gets a system member.

        Args:
            member_id: The ID of the member to be fetched.

        Returns:
            Member: The member with the given ID.

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

    async def new_member(self, **kwargs) -> Member:
        """Creates a new member of one's system.

        Note:
            The system's `authorization token`_ must be set in order to use :meth:`new_member`.

        Args:
            name: Name of the new member
            **kwargs: Any number of keyworded patchable values from `PluralKit's member model`_.
        
        Keyword Args:
            display_name (Optional[str]): New display name of the member. Default is None.
            description (Optional[str]): New description of the member. Default is None.
            pronouns (Optional[str]): New pronouns of the member. Default is None.
            color (Union[Color,str,None]): New color of the member. If a string, must be formatted
                as a 6-character hex string (e.g. ``"ff7000"``), sans the # symbol. Default is
                ``None``.
            avatar_url (Optional[str]): New avatar URL for the member. Default is None.
            birthday (Union[Timestamp,str]): New birthdate of the member. If a string, must be
                formatted as ``YYYY-MM-DD``, in which case, year of ``0001`` or ``0004`` represents
                a hidden year. Default is None.
            proxy_tags (Union[ProxyTags,Sequence[ProxyTag],Sequence[Dict[str,str]]]): New proxy
                tags of the member. May be a `~v1.models.ProxyTags` object, a sequence of
                `~v1.models.ProxyTag` objects, or a sequence of Python dictionaries with the
                keys "prefix" and "suffix". Default is an empty set of proxy tags.
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message. Default is ``False``.
            visibility (Union[Privacy,str,None]): New visibility privacy for the member. Must be
                either :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`.
                Default is public.
            name_privacy (Union[Privacy,str,None]): New name privacy for the member. Must be either
                :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. Default is
                public.
            description_privacy (Union[Privacy,str,None]): New description privacy for the member.
                Must be either :attr:`~v1.models.Privacy.PUBLIC` or
                :attr:`~v1.models.Privacy.PRIVATE`. Default is public.
            avatar_privacy (Union[Privacy,str,None]): New avatar privacy for the member. Must be
                either :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`.
                Default is public.
            pronoun_privacy (Union[Privacy,str]): New pronouns privacy for the member. Must be
                either :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`.
                Default is public.
            metadata_privacy (Union[Privacy,str]): New metadata (eg. creation timestamp, message
                count, etc.) privacy for the member. Must be either
                :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. Default is
                public.

        Returns:
            Member: The new member.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        .. _`authorization token`: https://pluralkit.me/api/#authentication
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

    async def edit_member(self, member_id: str, **kwargs) -> Member:
        """Edits a member of one's system.

        Note:
            The system's `authorization token`_ must be set in order to use :meth:`edit_member`.

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
            color (Union[Color,str,None]): New color of the member. If a string, must be formatted
                as a 6-character hex string (e.g. ``"ff7000"``), sans the # symbol. If ``None`` is
                passed, this field is cleared.
            avatar_url (Optional[str]): New avatar URL for the member. If ``None`` is passed, this
                field is cleared.
            birthday (Union[Birthday,str]): New birthdate of the member. If a string, must be
                formatted as ``YYYY-MM-DD``, in which case, a year of ``0001`` or ``0004``
                represents a hidden year. If ``None`` is passed, this field is cleared.
            proxy_tags (Union[ProxyTags,Sequence[ProxyTag],Sequence[Dict[str,str]]]): New proxy
                tags of the member. May be a `~v1.models.ProxyTags` object, a sequence of
                `~v1.models.ProxyTag` objects, or a sequence of Python dictionaries with the
                keys "prefix" and "suffix".
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message.
            visibility (Union[Privacy,str,None]): New visibility privacy for the member. Must be
                either :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. If
                ``None`` is passed, this field is reset to public.
            name_privacy (Union[Privacy,str,None]): New name privacy for the member. Must be either
                :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. If
                ``None`` is passed, this field is reset to public.
            description_privacy (Union[Privacy,str,None]): New description privacy for the member.
                Must be either :attr:`~v1.models.Privacy.PUBLIC` or
                :attr:`~v1.models.Privacy.PRIVATE`. If ``None`` is passed, this field is reset to
                public.
            avatar_privacy (Union[Privacy,str,None]): New avatar privacy for the member. Must be
                either :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. If
                ``None`` is passed, this field is reset to public.
            pronoun_privacy (Union[Privacy,str]): New pronouns privacy for the member. Must be
                either :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. If
                ``None`` is passed, this field is reset to public.
            metadata_privacy (Union[Privacy,str]): New metadata (eg. creation timestamp, message
                count, etc.) privacy for the member. Must be either
                :attr:`~v1.models.Privacy.PUBLIC` or :attr:`~v1.models.Privacy.PRIVATE`. If
                ``None`` is passed, this field is reset to public.

        Returns:
            Member: The updated member.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        .. _`authorization token`: https://pluralkit.me/api/#authentication
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
        
    async def delete_member(self, member_id: str):
        """Todo.
        """

        url = f"{self.SERVER}/m/{member_id}"

        async with aiohttp.ClientSession(trace_configs=None, headers=self.headers) as session:
            async with session.delete(url, ssl=True) as response:
                if response.status == 401:
                    if response.status == 401:
                        raise AuthorizationError()
                    elif response.status == 403:
                        raise AccessForbidden()

                    if response.status != 204: # catch-all
                        raise PluralKitException()

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

        url = f"{self.SERVER}{system_url}/switches"

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

        if self.token is None:
            raise AuthorizationError()
        
        url = f"{self.SERVER}/s/switches"
        payload = json.dumps({"members": members}, ensure_ascii=False)

        async with aiohttp.ClientSession(trace_configs=None, headers=self.content_headers) as session:
            async with session.post(url, data=payload, ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError()
                elif response.status == 403:
                    raise AccessForbidden()
                    
                if response.status != 204: # catch-all
                    raise PluralKitException()
    
    async def get_message(self, message: Union[str, Message]):
        """Todo.
        """
        
        if isinstance(message, (str, int)):
            url = f"{self.SERVER}/msg/{message}"
        elif isinstance(message, Message):
            url = f"{self.SERVER}/msg/{message.id}"

        async with aiohttp.ClientSession(trace_configs=None, headers=self.headers) as session:
            async with session.get(url, ssl=True) as response:
                if response.status == 401:
                    raise AuthorizationError()
                elif response.status == 403:
                    raise AccessForbidden()
                if response.status != 200: # catch-all
                    raise PluralKitException()
                else:
                    resp = await response.json()
                    
                    return Message.from_json(resp)
