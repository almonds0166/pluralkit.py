
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Awaitable, AsyncGenerator, Coroutine,
)

import asyncio

import httpx
import json
import datetime
from http.client import responses as RESPONSE_CODES

from .models import Message, System, Member, Switch, Timestamp
from .errors import *
from .utils import *

SERVER = "https://api.pluralkit.me/v1"

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
        id (Optional[str]): The five-letter lowercase ID of one's system if an authorization token
            is provided.
    """

    def __init__(self, token: Optional[str]=None, *,
        async_mode: bool=True,
        user_agent: Optional[str]=None
    ):
        self.async_mode = async_mode
        self.token = token
        self.headers = {}
        self.id = None
        if token:
            self.headers["Authorization"] = token
            if async_mode:
                loop = asyncio.get_event_loop()
                system = loop.run_until_complete(self._get_system())
            else:
                system = self.get_system() # type: ignore
            self.id = system.id
        self.user_agent = user_agent
        if user_agent:
            self.headers["User-Agent"] = user_agent
        self.content_headers = self.headers.copy()
        self.content_headers['Content-Type'] = "application/json"

    def get_system(self, system: Union[System,str,int,None]=None) \
    -> Union[System, Coroutine[Any,Any,System]]:
        """Return a system by its system ID or Discord user ID.

        Args:
            system: The system ID (as `str`), Discord user ID (as `int`), or `~v1.models.System`
                object of the system. If ``None``, returns the system of the client.

        Returns:
            System: The retrieved system.
        """
        awaitable = self._get_system(system)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _get_system(self, system: Union[System,str,int,None]=None) -> System:
        if system is None:
            if not self.token: raise AuthorizationError() # please pass in your token to the client
            # get own system
            url = f"{SERVER}/s"
        elif isinstance(system, System):
            # System object
            url = f"{SERVER}/s/{system.id}"
        elif isinstance(system, str):
            # system ID
            url = f"{SERVER}/s/{system}"
        elif isinstance(system, int):
            # Discord user ID
            url = f"{SERVER}/a/{system}"

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

            new_system = System.from_json(resp)

            return new_system
    
    def edit_system(self, system: System, **kwargs) -> Union[System, Coroutine[Any,Any,System]]:
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
        awaitable = self._edit_system(system, **kwargs)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _edit_system(self, system: Optional[System]=None, **kwargs) -> System:
        if self.token is None:
            raise AuthorizationError()

        url = f"https://api.pluralkit.me/v1/s"
        if system is not None and not kwargs:
            kwargs = system.json()
            del kwargs['id']
            del kwargs['created']
        elif system is not None and kwargs:
            kwargs_ = system.json()
            kwargs = kwargs_.update(kwargs)
        else:
            for key, value in kwargs.items():
                kwargs = await system_value(key=key, value=value)
        
        payload = json.dumps(kwargs, ensure_ascii=False)

        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.patch(url, data=payload)
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()

            system = System.from_json(resp)

            return system

    def get_fronters(self, system=None) \
    -> Union[Tuple[Timestamp, List[Member]], Coroutine[Any,Any,Tuple[Timestamp, List[Member]]]]:
        """Fetches the current fronters of a system.
        
        Args:
            system(Optional[Union[str, System]]): The system to fetch fronters from.
        
        Returns:
            Tuple[Timestamp, List[Member]]: The Timestamp object and the list of current fronters.
        """
        awaitable = self._get_fronters(system)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _get_fronters(self, system=None) -> Tuple[Timestamp, List[Member]]:
        if system is None: 
            url = f"{SERVER}/s/{self.id}/fronters"
        elif isinstance(system, str):
            url = f"{SERVER}/s/{system}/fronters"
        elif isinstance(system, System):
            url = f"{SERVER}/s/{system.id}/fronters"
        
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

    def get_members(self, system: Union[System,str,int,None]=None
    ) -> Union[List[Member], AsyncGenerator[Member,None]]:
        """Retrieve list of a system's members.

        Args:
            system: The system ID, Discord user ID, or System object of the system. If ``None``,
                returns a list of the client system's members.

        Yields:
            Member: The next system member.
        """
        awaitable = self._get_members(system)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(flatten(awaitable))
            return result

    async def _get_members(self, system: Union[System,str,int,None]=None) \
    -> AsyncGenerator[Member,None]:
        async with httpx.AsyncClient(headers=self.headers) as session:
            if system is None:
                # get own system
                url = f"{SERVER}/s/{self.id}/members"
            elif isinstance(system, System):
                # System object
                url = f"{SERVER}/s/{system.id}/members"
            elif isinstance(system, str):
                # system ID
                url = f"{SERVER}/s/{system}/members"
            elif isinstance(system, int):
                # Discord user ID

                system_info = await session.get(f"https://api.pluralkit.me/v1/a/{system}")
                system_ = System.from_json(system_info.json())
                url = f"{SERVER}/s/{system_.id}/members"

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
    
    def get_member(self, member_id: str) -> Union[Member, Coroutine[Any,Any,Member]]:
        """Gets a system member.

        Args:
            member_id: The ID of the member to be fetched.

        Returns:
            Member: The member with the given ID.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        """
        awaitable = self._get_member(member_id)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _get_member(self, member_id: str) -> Member:
        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.get(f"{SERVER}/m/{member_id}")
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 200:
                item = response.json()
                return Member.from_json(item)
            elif response.status_code == 404:
                raise MemberNotFound(member_id)
            else:
                raise Exception(f"Something went wrong with your request. You received a "
                        f"{response.status_code} http code, here is a list of possible http codes "
                        "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_client_errors")

    def new_member(self, **kwargs) -> Union[Member, Coroutine[Any,Any,Member]]:
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
        awaitable = self._new_member(**kwargs)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _new_member(self, **kwargs) -> Member:
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
        
        payload = json.dumps(kwargs, ensure_ascii=False)

        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.post(f"{SERVER}/m/", data=payload)
            if response.status_code == 401:
                raise AuthorizationError
            elif response.status_code == 200:
                item = response.json()
                return Member.from_json(item)
            else:
                raise Exception(f"Something went wrong with your request. You received a "
                        f"{response.status_code} http code, here is a list of possible http codes "
                        "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_client_errors")

    def edit_member(self, 
                    member_id: Union[str, Member], 
                    member: Optional[Member]=None, 
                    **kwargs) -> Union[Member, Coroutine[Any,Any,Member]]:
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
        
        awaitable = self._edit_member(member_id, member, **kwargs)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _edit_member(self, member_id: str, member: Optional[Member]=None, **kwargs) -> Member:
        if self.token is None:
            raise AuthorizationError()
        
        if isinstance(member, Member) and not kwargs:
            kwargs = member.json()
            del kwargs['id']
            del kwargs['created']
        elif isinstance(member, Member) and kwargs:
            kwargs_ = member.json()
            kwargs = kwargs_.update(kwargs)
        else:
            for key, value in kwargs.items():
                kwargs = await member_value(kwargs=kwargs, key=key, value=value)
        
        payload = json.dumps(kwargs, ensure_ascii=False)
        
        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.patch(f"{SERVER}/m/{member_id}", data=payload)
            if response.status_code == 401:
                raise AuthorizationError
            elif response.status_code == 200:
                item = response.json()
                return Member.from_json(item)
            else:
                raise Exception(f"Something went wrong with your request. You received a "
                        f"{response.status_code} http code, here is a list of possible http codes "
                        "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_client_errors")
    
    def delete_member(self, member_id: str) -> Union[None, Coroutine[Any,Any,None]]:
        """Deletes a member of one's system
        
        Note:
            The system's `authorization token`_ must be set in order to use :meth:`delete_member`.
        
        Args:
            member_id (str): The ID of the member to be deleted.

        .. _`authorization token`: https://pluralkit.me/api/#authentication
        """
        awaitable = self._delete_member(member_id)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _delete_member(self, member_id: str) -> None:
        url = f"{SERVER}/m/{member_id}"

        async with httpx.AsyncClient(headers=self.headers) as session:
            response = await session.delete(url)
            if response.status_code == 401:
                if response.status_code == 401:
                    raise AuthorizationError()
                elif response.status_code == 403:
                    raise AccessForbidden()

                if response.status_code != 204: # catch-all
                    raise HTTPError(response.status_code)

    def get_switches(self, system: Optional[System]=None) -> Union[List[Switch], AsyncGenerator[Switch,None]]:
        """Fetches the switch history of a system.
        
        Args:
            system (Optional[Union[str, System]])
            
        Yields:
            Switch: The next switch.
        """
        awaitable = self._get_switches(system)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(flatten(awaitable))
            return result
        
    async def _get_switches(self, system=None) -> AsyncGenerator[Switch,None]:
        if system is None:
            #Authorized system
            system_url = f"/s/{self.id}"
        elif isinstance(system, System):
            # System object
            system_url = f"/s/{system.id}"
        elif isinstance(system, str):
            # system ID
            system_url = f"/s/{system}"

        url = f"{SERVER}{system_url}/switches"

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

    def new_switch(self, members) -> Union[None, Coroutine[Any,Any,None]]:
        """Creates a new switch
        
        Note:
            The system's `authorization token`_ must be set in order to use :meth:`delete_member`.
        
        Args:
            members(Sequence[str]): A list of members that will be present in the new switch.

        Returns:
            Switch: The newly created switch.

        .. _`authorization token`: https://pluralkit.me/api/#authentication
        """
        awaitable = self._new_switch(members)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _new_switch(self, members: List[Union[str, Member]]) -> None:
        if self.token is None:
            raise AuthorizationError()
        
        url = f"{SERVER}/s/switches"
        
        members = [m.id if type(m) is Member else m for m in members]

        payload = json.dumps({"members": members}, ensure_ascii=False)
        
        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.post(url, data=payload)
            if response.status_code == 401:
                raise AuthorizationError()
            elif response.status_code == 403:
                raise AccessForbidden()
                
            if response.status_code != 204: # catch-all
                raise HTTPError(response.status_code)
    
    def get_message(self, message: Union[str, int, Message]) -> Union[Message, Coroutine[Any,Any,Message]]:
        """Fetches a message proxied by pluralkit
        
        Note:
            Messages proxied by pluralkit can be fetched either with the proxy message's id, or the
            id of the original message that triggered the proxy.
        
        Args:
            Message: The message to be fetched.
        """
        awaitable = self._get_message(message)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result
        
    async def _get_message(self, message: Union[str, int, Message]) -> Message:
        if isinstance(message, (str, int)):
            url = f"{SERVER}/msg/{message}"
        elif isinstance(message, Message):
            url = f"{SERVER}/msg/{message.id}"

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
