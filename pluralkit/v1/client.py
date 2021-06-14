
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
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

    async def get_system(self, system: Union[System,str,int,None]=None) -> System:
        """Return a system by its system ID or Discord user ID.

        Args:
            system: The system ID, Discord user ID, or System object of the system. If None, returns
                the system of the client.

        Returns:
            system (System): The desired system.
        """

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

                system = System.from_dict(resp)

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
                    member = Member.from_dict(item)

                    yield member

    async def edit_member(self, member_id: str, **kwargs) -> Member:
        """Edits a member of the system with the authorization token passed at initialization.

        Args:
            member_id: The ID of the member to be edited.
            **kwargs: Any number of keyworded patchable values from `PluralKit's member model`_.
        
        Keyword Args:
            name (Optional[str]): New name of the member. If ``None`` is passed, this field is
                cleared.
            display_name (Optional[str]): New display name of the member. If ``None`` is passed,
                this field is cleared.
            description (Optional[str]): New description of the member. If ``None`` is passed, this
                field is cleared.
            pronouns (Optional[str]): New pronouns of the member. If ``None`` is passed, this field
                is cleared.
            color (Union[Colour,str,None]): New color of the member. If a string, must be formatted
                as a 6-character hex string (e.g. "ff7000"), sans the # symbol. If ``None`` is
                passed, this field is cleared.
            avatar_url (str): New avatar URL for the member. If ``None`` is passed, this field is
                cleared.
            birthday (Union[datetime,str]): New birthdate of the member. If a string, must be
                formatted as ``YYYY-MM-DD``. A year of ``0001`` or ``0004`` represents a hidden
                year. If ``None`` is passed, this field is cleared.
            proxy_tags (Union[ProxyTags,Sequence[ProxyTag],Sequence[Dict[str,str]]]): New proxy
                tags of the member. May be a ProxyTags object, a sequence of ProxyTag objects, or a
                sequence of Python dictionaries with the keys "prefix" and "suffix".
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message.
            visibility (Optional[str]): New visibility privacy for the member. Must be either
                "public" or "private". If ``None`` is passed, this field is reset to "public".
            name_privacy (Optional[str]): New name privacy for the member. Must be either "public"
                or "private". If ``None`` is passed, this field is reset to "public".
            description_privacy (Optional[str]): New description privacy for the member. Must be
                either "public" or "private". If ``None`` is passed, this field is reset to
                "public".
            avatar_privacy (Optional[str]): New avatar privacy for the member. Must be either
                "public" or "private". If ``None`` is passed, this field is reset to "public".
            pronoun_privacy (Optional[str]): New pronouns privacy for the member. Must be either
                "public" or "private". If ``None`` is passed, this field is reset to "public".
            metadata_privacy (Optional[str]): New metadata (eg. creation timestamp, message count,
                etc.) privacy for the member. Must be either "public" or "private". If ``None`` is
                passed, this field is reset to "public".

        Returns:
            member (Member): Modified member object.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
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
                    return Member.from_dict(item)
