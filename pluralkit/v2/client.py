
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
from functools import wraps

import httpx

from .models import (
    Model,
    MemberId, SystemId, GroupId, SwitchId,
    Member, System, Group, Switch, Message,
    MemberGuildSettings, SystemGuildSettings,
    Timestamp,
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
            #if async_mode:
            #    loop = asyncio.get_event_loop()
            #    system = loop.run_until_complete(self._get_system())
            #else:
            #    system = self.get_system() # type: ignore
            #self.id = system.id
        self.content_headers = self.headers.copy()
        self.content_headers["Content-Type"] = "application/json"

    # ========================
    #  Private helper methods
    # ========================

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

    # abstract API http requester
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
        params: Optional[dict]=None, # for query strings
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
            kwargs = {}
            if params is not None: kwargs["params"] = params
            if payload is not None: kwargs["payload"] = payload
            response = await request_func(url, **kwargs)

            code = response.status_code
            returned = response.json()
            if code != expected_code:
                if code in error_lookups:
                    msg = "{code}: {messsage}".format(**returned)
                    error = error_lookups[code](msg)
                else:
                    error = HTTPError(code)
                raise error

            # convert received json to return type
            #print(returned)
            converted = ModelConstructor(returned)

        # return
        return converted

    # streamline the async_mode=True vs. False difference
    def _async_mode_handler(wrapped_function):
        @wraps(wrapped_function)
        def wrapped(instance, *args, **kwargs):
            awaitable = wrapped_function(instance, *args, **kwargs)
            if instance.async_mode:
                return awaitable
            else:
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(awaitable)
                return result
        return wrapped

    # ==============
    #  Main methods
    # ==============

    @_async_mode_handler
    def get_system(self, system: Union[SystemId,int,None]=None):
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}",
            System,
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            system=system,
        )

    @_async_mode_handler
    def get_member(self, member: Union[MemberId,str]):
        return self._request_something(
            "GET",
            "{SERVER}/members/{member_ref}",
            Member,
            200,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
        )

    @_async_mode_handler
    def get_group(self, group: Union[GroupId,str]):
        return self._request_something(
            "GET",
            "{SERVER}/groups/{group_ref}",
            Group,
            200,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
        )

    @_async_mode_handler
    def get_message(self, message: int):
        return self._request_something(
            "GET",
            "{SERVER}/messages/{message_ref}",
            Message,
            200,
            MESSAGE_ERROR_CODE_LOOKUP,
            message=message,
        )

    @_async_mode_handler
    def get_switches(self, system: Union[SystemId,int,None]=None, *,
        before: Timestamp=None,
        limit: int=None,
    ):
        """Get list of system switches.

        Returns at most 100 switches. To get more, specify using ``before`` parameter.

        Arguments:
            system: System ID to get switches from.

        Keyword arguments:
            before: Timestamp before which to get latest switches from. Default is None.
            limit: Number of switches to return. Default (and maximum) is 100.
        """
        params = {}
        if before is not None: params["before"] = before.json()
        if limit is not None: params["limit"] = limit
        if not params: params = None
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/switches",
            lambda list_: [Switch(item) for item in list_],
            200,
            GENERIC_ERROR_CODE_LOOKUP,
            system=system,
            params = params,
        )



