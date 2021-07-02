
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)

import asyncio
import httpx
import json
import datetime
from http.client import responses as RESPONSE_CODES

from .models import Message, System, Member, Switch, Timestamp
from .errors import *
from .utils import *
from . import endpoint

class Client:
    """Represents a client that interacts with the PluralKit API.

    Args:
        token: The PluralKit authorization token, received by the ``pk;token`` command.

    Keyword args:
        async_mode: Whether the client runs asynchronously (``True``, default) or not (``False``).
        user_agent: The User-Agent header to use with the API.

    Attributes:
        token (Optional[str]): The client's PluralKit authorization token.
        async_mode (bool): Whether the client runs asynchronously (``True``) or not (``False``).
        user_agent (Optional[str]): The User-Agent header used with the API.
        headers (Dict[str,str]): 
        content_headers (Dict[str,str]): 
    """

    SERVER = "https://api.pluralkit.me/v1"

    def __init__(self, token: Optional[str]=None, *,
        async_mode: bool=True,
        user_agent: Optional[str]=None
    ):
        self.async_mode = async_mode
        self._async = set()
        self.token = token
        self.headers = {}
        self.id = None
        if token:
            self.headers["Authorization"] = token
            if async_mode:
                loop = asyncio.get_event_loop()
                system = loop.run_until_complete(self.get_system())
            else:
                system = self.get_system()
            self.id = system.id
        self.user_agent = user_agent
        if user_agent:
            self.headers["User-Agent"] = user_agent
        self.content_headers = self.headers.copy()
        self.content_headers['Content-Type'] = "application/json"
    
    @staticmethod
    def _get_system_url(self, system) -> str:
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

    @endpoint.func
    async def get_system(self, system: Union[System,str,int,None]=None) -> System:
        """Return a system by its system ID or Discord user ID.

        Args:
            system: The system ID (as `str`), Discord user ID (as `int`), or `~v1.models.System`
                object of the system. If ``None``, returns the system of the client.

        Returns:
            System: The retrieved system.
        """
        url = Client._get_system_url(self, system)


        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(url)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 404:
                if isinstance(system, str):
                    raise SystemNotFound(system)
                elif isinstance(system, int):
                    raise DiscordUserNotFound(system)
                
                if response.status_code != 200: # catch-all
                    raise HTTPError(response.status_code)

            resp = response.json()

            system = System.from_json(resp)

            if url.endswith("/s"):
                # remember self ID for the future
                self._id = system.id

            return system
    
    @endpoint.func
    async def edit_system(self, **kwargs) -> System:
        """"Edits one's own system
        
        Note:
            Any fields not passed will retain their prior value.
            Any fields passed with null will clear or reset to the default.
            
        Args:
            **kwargs: Any number of keyworded patchable values from `PluralKit's system model`_.
            
        Keyword Args:
            name(str): The new system name.
            description(Optional[str]): The new system description.
            tag(Optional[str]): The new system tag.
            avatar_url(Optional[str]): The new system avatar.
            tz(Optional[str]): The timezone as a tzdb identifier, null will store "UTC"
            description_privacy(Optional[str]): The new system description privacy value
            member_list_privacy(Optional[str]): The new system member list privacy value
            front_privacy(Optional[str]): The new system front privacy value
            metadata_privacy(Optional[str]): The new system metadata privacy value

        Returns:
            System: The updated system.

        .. _`PluralKit's system model`: https://pluralkit.me/api/#system-model
        """

        if self.token is None:
            raise AuthorizationError()

        url = f"https://api.pluralkit.me/v1/s"
    
        for key, value in kwargs.items():
            kwargs = await system_value(key=key, value=value)
        
        json_object = json.dumps(kwargs, ensure_ascii=False)

        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.patch(url, data=json_object)
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()

            system = System.from_json(resp)

            return system

    @endpoint.func
    async def get_fronters(self, system=None) -> Tuple[Timestamp, List[Member]]:
        """Fetches the current fronters of a system.
        
        Args:
            system(Optional[Union[str, System]]): The system to fetch fronters from.
        
        Returns:
            Set(Timestamp, List[Member]): A set containing a Timestamp object and a list of current
            fronters in Member objects
        """
        
        if system is None: 
            url = f"{self.SERVER}/s/{self.id}/fronters"
        elif isinstance(system, str):
            url = f"{self.SERVER}/s/{system}/fronters"
        elif isinstance(system, System):
            url = f"{self.SERVER}/s/{system.id}/fronters"
        
        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(url)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 403:
                raise AccessForbidden()
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)
            else:
                resp = response.json()
                member_list = []
                for fronter in resp['members']:
                    member_list.append(Member.from_json(fronter))
                timestamp = Timestamp.from_json(resp['timestamp'])
                return (timestamp, member_list)

    @endpoint.iter
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
            url = f"{self.SERVER}/s/{self.id}/members"
        elif isinstance(system, System):
            # System object
            url = f"{self.SERVER}/s/{system.id}/members"
        elif isinstance(system, str):
            # system ID
            url = f"{self.SERVER}/s/{system}/members"
        elif isinstance(system, int):
            # Discord user ID
            system = await self._get_system(system)
            url = f"{self.SERVER}/s/{system.id}/members"

        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(url)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 403:
                raise AccessForbidden()
            elif response.status_code == 404:
                if isinstance(system, str):
                    raise SystemNotFound(system)
                elif isinstance(system, int):
                    raise DiscordUserNotFound(system)
                
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()

            for item in resp:
                member = Member.from_json(item)

                yield member
    
    @endpoint.func
    async def get_member(self, member_id: str) -> Member:
        """Gets a system member.

        Args:
            member_id: The ID of the member to be fetched.

        Returns:
            Member: The member with the given ID.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        """
        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(f"{self.SERVER}/m/{member_id}")
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 200:
                item = response.json()
                return Member.from_json(item)
            else:
                raise Exception(f"Something went wrong with your request. You received a "
                        f"{response.status_code} http code, here is a list of possible http codes "
                        "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_client_errors")

    @endpoint.func
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
        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.post(f"{self.SERVER}/m/", data=json_payload)
            if response.status_code == 401:
                raise AuthorizationError
            elif response.status_code == 200:
                item = response.json()
                return Member.from_json(item)
            else:
                raise Exception(f"Something went wrong with your request. You received a "
                        f"{response.status_code} http code, here is a list of possible http codes "
                        "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_client_errors")

    @endpoint.func
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
        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.patch(f"{self.SERVER}/m/{member_id}", data=json_payload)
            if response.status_code == 401:
                raise AuthorizationError
            elif response.status_code == 200:
                item = response.json()
                return Member.from_json(item)
            else:
                raise Exception(f"Something went wrong with your request. You received a "
                        f"{response.status_code} http code, here is a list of possible http codes "
                        "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_client_errors")
        
    @endpoint.func
    async def delete_member(self, member_id) -> None:
        """Deletes a member of one's system
        
        Note:
            The system's `authorization token`_ must be set in order to use :meth:`delete_member`.
        
        Args:
            member_id (str): The ID of the member to be deleted.

        .. _`authorization token`: https://pluralkit.me/api/#authentication
        """

        url = f"{self.SERVER}/m/{member_id}"

        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.delete(url)
            if response.status_code == 401:
                if response.status_code == 401:
                    raise AuthorizationError()
                elif response.status_code == 403:
                    raise AccessForbidden()

                if response.status_code != 204: # catch-all
                    raise HTTPError(response.status_code)

    @endpoint.iter
    async def get_switches(self, system=None):
        """Fetches the switch history of a system.
        
        Args:
            system (Optional[Union[str, System]])
            
        Yields:
             Switch: The next switch.
        """
        
        if system is None:
            #Authorized system
            system_url = f"/s/{self.id}"
        elif isinstance(system, System):
            # System object
            system_url = f"/s/{system.id}"
        elif isinstance(system, str):
            # system ID
            system_url = f"/s/{system}"

        url = f"{self.SERVER}{system_url}/switches"

        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(url)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 403:
                raise AccessForbidden()
            elif response.status_code == 404:
                if isinstance(system, str):
                    raise SystemNotFound(system)
                elif isinstance(system, int):
                    raise DiscordUserNotFound(system)
                
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()

            for item in resp:
                switch = Switch.from_json(item)
                yield switch

    @endpoint.func
    async def new_switch(self, members) -> Switch:
        """Creates a new switch
        
        Note:
            The system's `authorization token`_ must be set in order to use :meth:`delete_member`.
        
        Args:
            members(Sequence[str]): A list of members that will be present in the new switch.

        Returns:
            Switch: The newly created switch.

        .. _`authorization token`: https://pluralkit.me/api/#authentication
        """

        if self.token is None:
            raise AuthorizationError()
        
        url = f"{self.SERVER}/s/switches"
        payload = json.dumps({"members": members}, ensure_ascii=False)

        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.post(url, data=payload)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 403:
                raise AccessForbidden()
                
            if response.status_code != 204: # catch-all
                raise HTTPError(response.status_code)
    
    @endpoint.func
    async def get_message(self, message: Union[str, int, Message]) -> Message:
        """Fetches a message proxied by pluralkit
        
        Note:
            Messages proxied by pluralkit can be fetched either with the proxy message's id, or the
            id of the original message that triggered the proxy.
        
        Args:
            Message: The message to be fetched.
        """
        
        if isinstance(message, (str, int)):
            url = f"{self.SERVER}/msg/{message}"
        elif isinstance(message, Message):
            url = f"{self.SERVER}/msg/{message.id}"

        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(url)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 403:
                raise AccessForbidden()
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)
            else:
                resp = response.json()
                
                return Message.from_json(resp)
