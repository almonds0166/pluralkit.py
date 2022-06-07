
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Awaitable, AsyncGenerator, Coroutine,
    Callable,
)
import datetime
import asyncio
from http.client import responses as RESPONSE_CODES

import httpx

from .models import (
    Model,
    MemberId, SystemId, GroupId, SwitchId,
    Member, System, Group, Switch, Message,
    MemberGuildSettings, SystemGuildSettings,
)
from .errors import *

SERVER = "https://api.pluralkit.me/v2"

class Client:
    """Represents a client that interacts with the PluralKit API.

    Args:
        token

    Keyword args:
        async_mode
        user_agent

    Attributes:
        token
        async_mode
        headers
        content_headers
        id
    """
    def __init__(self, token: Optional[str]=None, *,
        async_mode: bool=True,
        user_agent: Optional[str]=None,
    ):
        # core factors
        self.async_mode = async_mode
        self.token = token
        self.id = None

        # initialize rate limit handling
        self._rate_limit_remaining = 0
        self._rate_limit_reset_time = datetime.datetime.now()

        # set up headers
        self.headers = {}
        if user_agent: self.headers["User-Agent"] = user_agent
        if token:
            self.headers["Authorization"] = token
            if async_mode:
                loop = asyncio.get_event_loop()
                system = loop.run_until_complete(self._get_system())
            else:
                system = self.get_system() # type: ignore
            self.id = system.id
        self.content_headers = self.headers.copy()
        self.content_headers["Content-Type"] = "application/json"

    async def _respect_rate_limit(self):
        """Respects the rate limit by waiting if necessary."""
        if self._rate_limit_remaining == 0:
            now = datetime.datetime.now()
            if self._rate_limit_reset_time < now:
                self._rate_limit_remaining = 2
                self._rate_limit_reset_time = now + datetime.timedelta(seconds=1)
            else:
                await asyncio.sleep(self._rate_limit_reset_time - now)
                self._rate_limit_remaining = 2
                self._rate_limit_reset_time = now + datetime.timedelta(seconds=1)
 
    def _update_rate_limits(self, headers):
        """Updates the rate limits based on the returned headers."""
        if "X-RateLimit-Remaining" in headers:
            self._rate_limit_remaining = int(headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in headers:
            self._rate_limit_reset_time = datetime.datetime.fromtimestamp(int(headers["X-RateLimit-Reset"]))

    # ==============
    #  Main methods
    # ==============

    async def _request_something(self,
        # required positional arguments
        kind: str,
        url_template: str,
        ModelConstructor,
        expected_code: int,
        error_lookups: dict,
        *,
        # reference IDs
        system: Union[SystemId,int,None]=None, # (int too, because it can be a Discord user ID)
        member: Optional[MemberId]=None,
        group: Optional[GroupId]=None,
        switch: Optional[SwitchId]=None,
        message: Optional[int]=None,
        # optional payload
        payload: Optional[dict]=None,
    ):
        # put together url from given arguments
        pieces = {"SERVER": SERVER}

        if "system_ref" in url_template:
            if system is None:
                if not self.token: raise Unauthorized() # pass in your token please
                pieces["system_ref"] = "@me"
            else:
                pieces["system_ref"] = str(system)

        map_ = {
            "member_ref": member,
            "group_ref": group,
            "switch_ref": switch,
            "message_ref": message
        }
        for ref_name, arg in map_.items():
            if ref_name in url_template:
                pieces[ref_name] = str(arg)

        url = url_template.format(**pieces)

        # make the request
        async with httpx.AsyncClient(headers=self.headers) as session:
            request_func = getattr(session, kind.lower()) # nice
            if payload is None:
                response = await request_func(url)
            else:
                response = await request_func(url, data=payload)

            code = response.status_code
            if code != expected_code:
                error = error_lookups.get(code, HTTPError)()
                raise error

            # convert received json to return type
            returned = response.json()
            #print(returned)
            converted = ModelConstructor(returned)

        # return
        return converted

    SYSTEM_ERROR_CODE_LOOKUP = {
        401: ValidationError,
        403: ValidationError,
        404: SystemNotFound,
    }

    MEMBER_ERROR_CODE_LOOKUP = {
        401: ValidationError,
        403: ValidationError,
        404: MemberNotFound,
    }

    GROUP_ERROR_CODE_LOOKUP = {
        401: ValidationError,
        403: ValidationError,
        404: GroupNotFound,
    }

    MESSAGE_ERROR_CODE_LOOKUP = {
        401: ValidationError,
        403: ValidationError,
        404: MessageNotFound,
    }

    def get_system(self, system: Union[SystemId,int,None]=None):
        """
        """
        awaitable = self._get_system(system)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    def _get_system(self, system: Union[SystemId,int,None]=None):
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}",
            System,
            200,
            self.SYSTEM_ERROR_CODE_LOOKUP,
            system=system,
        )

    #async def _update_system(self, system: Union[SystemId])
    
    def get_member(self, member: Union[MemberId,str]):
        """
        """
        awaitable = self._get_member(member)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    def _get_member(self, member: Union[MemberId,str]):
        return self._request_something(
            "GET",
            "{SERVER}/members/{member_ref}",
            Member,
            200,
            self.MEMBER_ERROR_CODE_LOOKUP,
            member=member,
        )

    def get_group(self, group: Union[GroupId,str]):
        """
        """
        awaitable = self._get_group(group)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    def _get_group(self, group: Union[GroupId,str]):
        return self._request_something(
            "GET",
            "{SERVER}/groups/{group_ref}",
            Group,
            200,
            self.GROUP_ERROR_CODE_LOOKUP,
            group=group,
        )

    def get_message(self, message: int):
        """
        """
        awaitable = self._get_message(message)
        if self.async_mode:
            return awaitable
        else:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(awaitable)
            return result

    def _get_message(self, message: int):
        return self._request_something(
            "GET",
            "{SERVER}/messages/{message_ref}",
            Message,
            200,
            self.MESSAGE_ERROR_CODE_LOOKUP,
            message=message,
        )



