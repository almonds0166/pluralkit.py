
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
    MemberId, SystemId, GroupId,SwitchId,
    Member, System, Group, Switch, Message,
    MemberGuildSettings, SystemGuildSettings,
    Timestamp
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
                system = self._get_system() # type: ignore
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
        expected_type: Model,
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
            print(returned)
            converted = expected_type.from_json(returned)
            print(converted)
        # return
        return converted

    
    
    async def _get_system(self, system: Union[System,str,int,None]=None):
        
        return await self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}",
            System,
            200,
            {
                404: SystemNotFound,
            },
            system=system,
        )

    async def _update_system(self, system: Union[SystemId,int,None]=None, **kwargs):
        return await self._request_something(
            "PATCH",
            "{SERVER}/systems/{system_ref}",
            System,
            200,
            {
                401: Unauthorized,
                403: NotOwnError,
                404: SystemNotFound,
            },
            system=system,
        )

    async def _get_fronters(self, system=None) -> Tuple[Timestamp, List[Member]]:
        return await self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/fronters",
            Member,
            200,
            {
                404: SystemNotFound,
            },
            system=system,
        )
            

