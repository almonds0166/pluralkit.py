
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Awaitable, AsyncGenerator, Coroutine,
)
import collections
import datetime
import json
import asyncio
from http.client import responses as RESPONSE_CODES

import httpx

from .models import Message, System, Member, Switch, Timestamp
from .errors import *
from .utils import *

SERVER = "https://api.pluralkit.me/v1"
RATE_LIMIT_THROTTLE = 0.1 # seconds

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
        id (Optional[str]): The five-letter lowercase ID of one's system if an authorization token
            is provided.
    """
    def __init__(self, token: Optional[str]=None, *,
        async_mode: bool=True,
        user_agent: Optional[str]=None
    ):
        self._calls_queue = collections.deque()
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
        self.content_headers["Content-Type"] = "application/json"

    def _num_calls_in_last_half_second(self):
        half_second = datetime.timedelta(seconds=0.5)
        while len(self._calls_queue) \
                and datetime.datetime.now() - self._calls_queue[-1] > half_second:
            self._calls_queue.pop()

        return len(self._calls_queue)

    async def _respect_rate_limit(self):
        while self._num_calls_in_last_half_second() >= 1:
            await asyncio.sleep(RATE_LIMIT_THROTTLE)

        self._calls_queue.append(datetime.datetime.now())

    def get_system(self, system: Union[System,str,int,None]=None) \
    -> Union[System, Coroutine[Any,Any,System]]:
        """Return a system by its system ID or Discord user ID.

        Args:
            system: The system ID (as `str`), Discord user ID (as `int`), or `System` object of the
                system. If ``None``, returns the system of the client.

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

        await self._respect_rate_limit()

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
    
    def edit_system(self, system: Optional[System]=None, **kwargs) \
    -> Union[System, Coroutine[Any,Any,System]]:
        """Edits one's own system

        Note:
            The system's `authorization token`_ must be set in order to use this method.

        If a `System` object is provided, this method will use the attributes of that
        object to edit one's system. If *both* a System object and some keyword arguments are
        passed, the keyword arguments will take priority.

        Args:
            system: The optional object to transfer system attributes from.
            **kwargs: Any number of keyworded patchable values from `PluralKit's system model`_.

        Note:
            Any fields not passed will retain their prior value. Any fields passed with ``None``
            will clear or reset to the default.

        Keyword Args:
            name (Optional[str]): The new system name.
            description (Optional[str]): The new system description.
            tag (Optional[str]): The new system tag.
            avatar_url (Optional[str]): The new system avatar.
            tz (Union[Timezone,str,None]): The timezone as a tzdb identifier. Passing `None` will
                reset this field to "UTC".
            description_privacy (Union[Privacy,str,None]): The new system description privacy.
            member_list_privacy (Union[Privacy,str,None]): The new system member list privacy.
            front_privacy (Union[Privacy,str,None]): The new system front privacy.
            metadata_privacy (Union[Privacy,str,None]): The new system metadata privacy.

        Returns:
            System: The updated system.

        .. _`PluralKit's system model`: https://pluralkit.me/api/#system-model
        .. _`authorization token`: https://pluralkit.me/api/#authentication
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
            raise AuthorizationError() # catches a 401 before it happens

        if system is not None:
            kwargs_ = system.json()
            kwargs_.update(kwargs)
            kwargs = kwargs_

        if "id" in kwargs:
            del kwargs["id"]
        if "created" in kwargs:
            del kwargs["created"]

        for key, value in kwargs.items():
            await system_value(key=key, value=value)
        
        payload = json.dumps(kwargs, ensure_ascii=False)

        await self._respect_rate_limit()

        async with httpx.AsyncClient(headers=self.content_headers) as session:
            response = await session.patch(f"{SERVER}/s", data=payload)
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()
            system = System.from_json(resp)
            return system

    def get_fronters(self, system=None) \
    -> Union[Tuple[Timestamp, List[Member]], Coroutine[Any,Any,Tuple[Timestamp, List[Member]]]]:
        """Fetches the current fronters of a system.
        
        Args:
            system (Optional[Union[str,System,int]]): The system to fetch fronters from. Can be a
                System object, the five-letter lowercase system ID as a string, or the Discord user
                ID corresponding to a system. If ``None``, fetches the fronters of the system
                associated with the client.

        Note:
            Passing a Discord user ID takes an extra request. For this reason, it's perhaps better
            practice to cache the system ID associated with Discord accounts using
            `Client.get_system` first.
        
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
        async with httpx.AsyncClient(headers=self.headers) as session:
            if system is None:
                # get own system
                url = f"{SERVER}/s/{self.id}/fronters"
            elif isinstance(system, System):
                # System object
                url = f"{SERVER}/s/{system.id}/fronters"
            elif isinstance(system, str):
                # system ID
                url = f"{SERVER}/s/{system}/fronters"
            elif isinstance(system, int):
                # Discord user ID

                await self._respect_rate_limit()
                response = await session.get(f"{SERVER}/a/{system}")

                if response.status_code == 401:
                    raise AuthorizationError()

                if response.status_code == 404:
                    raise DiscordUserNotFound(system)
                    
                if response.status_code != 200: # catch-all
                    raise HTTPError(response.status_code)

                system_ = System.from_json(system_info.json())
                url = f"{SERVER}/s/{system_.id}/fronters"

            await self._respect_rate_limit()
            response = await session.get(url)

            if response.status_code == 401:
                raise AuthorizationError()

            if response.status_code == 403:
                raise AccessForbidden()

            if response.status_code == 404:
                if isinstance(system, System):
                    raise SystemNotFound(system.id)
                raise SystemNotFound(system)

            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()
            member_list = []
            for fronter in resp["members"]:
                member_list.append(Member.from_json(fronter))
            timestamp = Timestamp.from_json(resp["timestamp"])
            return (timestamp, member_list)

    def get_members(self, system: Union[System,str,int,None]=None
    ) -> Union[List[Member], AsyncGenerator[Member,None]]:
        """Retrieve list of a system's members.

        Args:
            system (Optional[Union[str,System,int]]): The system to fetch members from. Can be a
                System object, the five-letter lowercase system ID as a string, or the Discord user
                ID corresponding to a system. If ``None``, fetches the members of the system
                associated with the client.

        Note:
            Passing a Discord user ID takes an extra request. For this reason, it's perhaps better
            practice to cache the system ID associated with Discord accounts using
            `Client.get_system` first.

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

                await self._respect_rate_limit()
                response = await session.get(f"{SERVER}/a/{system}")

                if response.status_code == 401:
                    raise AuthorizationError()

                if response.status_code == 404:
                    raise DiscordUserNotFound(system)
                    
                if response.status_code != 200: # catch-all
                    raise HTTPError(response.status_code)

                system_ = System.from_json(response.json())
                url = f"{SERVER}/s/{system_.id}/members"

            await self._respect_rate_limit()
            response = await session.get(url)

            if response.status_code == 401:
                raise AuthorizationError()

            if response.status_code == 403:
                raise AccessForbidden()

            if response.status_code == 404:
                if isinstance(system, System):
                    raise SystemNotFound(system.id)
                raise SystemNotFound(system)
                
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
            await self._respect_rate_limit()
            response = await session.get(f"{SERVER}/m/{member_id}")

            if response.status_code == 404:
                raise MemberNotFound(member_id)

            if response.status_code != 200:
                raise HTTPError(response.status_code)
            
            resp = response.json()
            return Member.from_json(resp)

    def new_member(self, name: str, **kwargs) -> Union[Member, Coroutine[Any,Any,Member]]:
        """Creates a new member of one's system.

        Note:
            The system's `authorization token`_ must be set in order to use this method.

        Args:
            name: Name of the new member.
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
                tags of the member. May be a `ProxyTags` object, a sequence of `ProxyTag` objects,
                or a sequence of Python dictionaries with the keys "prefix" and "suffix". Default
                is an empty set of proxy tags.
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message. Default is ``False``.
            visibility (Union[Privacy,str,None]): New visibility privacy for the member. Must be
                either `Privacy.PUBLIC` or `Privacy.PRIVATE`. Default is public.
            name_privacy (Union[Privacy,str,None]): New name privacy for the member. Must be either
                `Privacy.PUBLIC` or `Privacy.PRIVATE`. Default is public.
            description_privacy (Union[Privacy,str,None]): New description privacy for the member.
                Must be either `Privacy.PUBLIC` or `Privacy.PRIVATE`. Default is public.
            avatar_privacy (Union[Privacy,str,None]): New avatar privacy for the member. Must be
                either `Privacy.PUBLIC` or `Privacy.PRIVATE`. Default is public.
            pronoun_privacy (Union[Privacy,str]): New pronouns privacy for the member. Must be
                either `Privacy.PUBLIC` or `Privacy.PRIVATE`. Default is public.
            metadata_privacy (Union[Privacy,str]): New metadata (eg. creation timestamp, message
                count, etc.) privacy for the member. Must be either `Privacy.PUBLIC` or
                `Privacy.PRIVATE`. Default is public.

        Returns:
            Member: The new member.

        .. _`PluralKit's member model`: https://pluralkit.me/api/#member-model
        .. _`authorization token`: https://pluralkit.me/api/#authentication
        """
        awaitable = self._new_member(name, **kwargs)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _new_member(self, name: str, **kwargs) -> Member:
        if self.token is None:
            raise AuthorizationError()

        kwargs["name"] = name

        for key, value in kwargs.items():
            kwargs = await member_value(kwargs=kwargs, key=key, value=value)
        
        payload = json.dumps(kwargs, ensure_ascii=False)

        async with httpx.AsyncClient(headers=self.content_headers) as session:
            
            await self._respect_rate_limit()
            response = await session.post(f"{SERVER}/m/", data=payload)

            if response.status_code == 401:
                raise AuthorizationError

            if response.status_code != 200:
                raise HTTPError(response.status_code)

            resp = response.json()
            return Member.from_json(resp)

    def edit_member(self, 
                    member_id: Union[str, Member], 
                    member: Optional[Member]=None, 
                    **kwargs) -> Union[Member, Coroutine[Any,Any,Member]]:
        """Edits a member of one's system.

        Note:
            The system's `authorization token`_ must be set in order to use this method.

        If a `Member` object is provided, this method will use the attributes of that
        object to edit the member. If *both* a Member object and some keyword arguments are
        passed, the keyword arguments will take priority.

        Args:
            member_id: The member to be edited. Can be a Member object or the member ID as a
                string.
            member: Optional Member object representing the member with updated attributes.
            **kwargs: Any number of keyworded patchable values from `PluralKit's member model`_.
        
        Note:
            Any fields not passed will retain their prior value. Any fields passed with ``None``
            will clear or reset to the default.

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
                tags of the member. May be a `ProxyTags` object, a sequence of `ProxyTag` objects,
                or a sequence of Python dictionaries with the keys "prefix" and "suffix".
            keep_proxy (bool): New truth value for whether to display the member's proxy tags in
                the proxied message.
            visibility (Union[Privacy,str,None]): New visibility privacy for the member. Must be
                either `Privacy.PUBLIC` or `Privacy.PRIVATE`. If ``None`` is passed, this field is
                reset to public.
            name_privacy (Union[Privacy,str,None]): New name privacy for the member. Must be either
                `Privacy.PUBLIC` or `Privacy.PRIVATE`. If ``None`` is passed, this field is reset
                to public.
            description_privacy (Union[Privacy,str,None]): New description privacy for the member.
                Must be either `Privacy.PUBLIC` or `Privacy.PRIVATE`. If ``None`` is passed, this
                field is reset to public.
            avatar_privacy (Union[Privacy,str,None]): New avatar privacy for the member. Must be
                either `Privacy.PUBLIC` or `Privacy.PRIVATE`. If ``None`` is passed, this field is
                reset to public.
            pronoun_privacy (Union[Privacy,str]): New pronouns privacy for the member. Must be
                either `Privacy.PUBLIC` or `Privacy.PRIVATE`. If ``None`` is passed, this field is
                reset to public.
            metadata_privacy (Union[Privacy,str]): New metadata (eg. creation timestamp, message
                count, etc.) privacy for the member. Must be either `Privacy.PUBLIC` or
                `Privacy.PRIVATE`. If ``None`` is passed, this field is reset to public.

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

        if isinstance(member, Member):
            kwargs_ = member.json()
            kwargs_.update(kwargs)
            kwargs = kwargs_

        if "id" in kwargs:
            del kwargs["id"]
        if "created" in kwargs:
            del kwargs["created"]

        for key, value in kwargs.items():
            kwargs = await member_value(kwargs=kwargs, key=key, value=value)
        
        payload = json.dumps(kwargs, ensure_ascii=False)
        
        async with httpx.AsyncClient(headers=self.content_headers) as session:
            
            await self._respect_rate_limit()
            response = await session.patch(f"{SERVER}/m/{member_id}", data=payload)
            
            if response.status_code == 401:
                raise AuthorizationError

            if response.status_code != 200:
                raise HTTPError(response.status_code)

            resp = response.json()
            return Member.from_json(resp)

    def delete_member(self, member_id: Union[str,Member]) \
    -> Union[None, Coroutine[Any,Any,None]]:
        """Deletes a member of one's system
        
        Note:
            The system's `authorization token`_ must be set in order to use this method.
        
        Args:
            member_id: The member to be deleted. Can be a Member object or the member ID as a
                string.

        Returns:
            `NoneType`: None

        .. _`authorization token`: https://pluralkit.me/api/#authentication
        """
        awaitable = self._delete_member(member_id)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    async def _delete_member(self, member_id: Union[str,Member]) -> None:
        url = f"{SERVER}/m/{member_id}"

        async with httpx.AsyncClient(headers=self.headers) as session:
    
            await self._respect_rate_limit()
            response = await session.delete(url)

            if response.status_code == 401:
                raise AuthorizationError()

            if response.status_code == 403:
                raise AccessForbidden()

            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

        return None

    def get_switches(self, system: Optional[Union[System,str]]=None) \
    -> Union[List[Switch], AsyncGenerator[Switch,None]]:
        """Fetches the switch history of a system.
        
        Args:
            system: The system to fetch switch history from. Can be a System object, the
                five-letter lowercase system ID as a string, or the Discord user ID corresponding
                to a system. If ``None``, fetches the switch history of the system associated with
                the client.

        Note:
            Passing a Discord user ID takes an extra request. For this reason, it's perhaps better
            practice to cache the system ID associated with Discord accounts using
            `Client.get_system` first.
            
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
        async with httpx.AsyncClient(headers=self.headers) as session:
            if system is None:
                # get own system
                url = f"{SERVER}/s/{self.id}/switches"
            elif isinstance(system, System):
                # System object
                url = f"{SERVER}/s/{system.id}/switches"
            elif isinstance(system, str):
                # system ID
                url = f"{SERVER}/s/{system}/switches"
            elif isinstance(system, int):
                # Discord user ID

                await self._respect_rate_limit()
                response = await session.get(f"{SERVER}/a/{system}")

                if response.status_code == 401:
                    raise AuthorizationError()

                if response.status_code == 404:
                    raise DiscordUserNotFound(system)
                    
                if response.status_code != 200: # catch-all
                    raise HTTPError(response.status_code)

                system_ = System.from_json(system_info.json())
                url = f"{SERVER}/s/{system_.id}/switches"

            await self._respect_rate_limit()
            response = await session.get(url)

            if response.status_code == 401:
                raise AuthorizationError()

            if response.status_code == 403:
                raise AccessForbidden()
            
            if response.status_code == 404:
                if isinstance(system, System):
                    raise SystemNotFound(system.id)
                raise SystemNotFound(system)
                
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()
            for item in resp:
                switch = Switch.from_json(item)
                yield switch

    def new_switch(self, members) -> Union[None, Coroutine[Any,Any,None]]:
        """Creates a new switch.
        
        Note:
            The system's `authorization token`_ must be set in order to use :meth:`delete_member`.
        
        Args:
            members (Sequence[Union[Member,str]]): A list of members that will be present in the
                new switch.

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
            
            await self._respect_rate_limit()
            response = await session.post(url, data=payload)

            if response.status_code == 401:
                raise AuthorizationError()
            
            if response.status_code == 403:
                raise AccessForbidden()
                
            if response.status_code != 204: # catch-all
                raise HTTPError(response.status_code)

        return None
    
    def get_message(self, message: Union[str, int, Message]) \
    -> Union[Message, Coroutine[Any,Any,Message]]:
        """Fetches a message proxied by pluralkit
        
        Note:
            Messages proxied by pluralkit can be fetched either with the proxy message's id, or the
            id of the original message that triggered the proxy.
        
        Args:
            Message: The message to be fetched. Can be a Discord message ID (as a string or
                integer) or a Message object.

        Returns:
            Message: The message object.
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

            await self._respect_rate_limit()
            response = await session.get(url)

            if response.status_code == 401:
                raise AuthorizationError()
            
            if response.status_code == 403:
                raise AccessForbidden()
            
            if response.status_code != 200: # catch-all
                raise HTTPError(response.status_code)

            resp = response.json()
            return Message.from_json(resp)
