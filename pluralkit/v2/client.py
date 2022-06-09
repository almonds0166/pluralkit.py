
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
    MemberGuildSettings, SystemGuildSettings, SystemSettings,
    Timestamp,
    _PATCHABLE_SYSTEM_KEYS,
    _PATCHABLE_MEMBER_KEYS,
    _PATCHABLE_GROUP_KEYS,
    _PATCHABLE_SWITCH_KEYS,
    _PATCHABLE_SYSTEM_SETTINGS_KEYS,
    _PATCHABLE_SYSTEM_GUILD_SETTINGS_KEYS,
    _PATCHABLE_MEMBER_GUILD_SETTINGS_KEYS,
    _PRIVACY_ASSOCIATED_KEYS,
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
        guild_id: Optional[int]=None,
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
            "message_ref": message,
            "guild_id": guild_id,
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
            if payload is not None: kwargs["json"] = payload
            response = await request_func(url, **kwargs)

            code = response.status_code
            returned = response.json() if response.text else ""
            if code != expected_code:
                if code in error_lookups:
                    if isinstance(returned, dict) and "message" in returned:
                        msg = "{code}: {message}".format(**returned)
                    else:
                        msg = f"{code}: {response.text!r}" if response.text else f"{code}"
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

    # 
    #  get
    # 

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
            params=params,
        )

    @_async_mode_handler
    def get_fronters(self, system: Union[SystemId,int,None]=None) \
    -> Sequence[Member]:
        """Get list of current fronters.
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/fronters",
            lambda json: [Member(item) for item in json["members"]],
            200,
            GENERIC_ERROR_CODE_LOOKUP,
            system=system,
        )

    @_async_mode_handler
    def get_switch(self, switch: Union[SwitchId,str], system: Union[SystemId,int,None]=None):
        """
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/switches/{switch_ref}",
            Switch,
            200,
            SWITCH_ERROR_CODE_LOOKUP,
            system=system,
            switch=switch,
        )

    @_async_mode_handler
    def get_members(self, system: Union[SystemId,int,None]=None) -> Sequence[Member]:
        """
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/members",
            lambda list_: [Member(m) for m in list_],
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            system=system,
        )

    @_async_mode_handler
    def get_member_groups(self, member: Union[Member,str]) -> Sequence[Group]:
        """
        """
        return self._request_something(
            "GET",
            "{SERVER}/members/{member_ref}/groups",
            lambda list_: [Group(g) for g in list_],
            200,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
        )

    @_async_mode_handler
    def get_system_groups(self, system: Union[SystemId,int,None]=None) -> Sequence[Group]:
        """
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/groups",
            lambda list_: [Group(g) for g in list_],
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            system=system,
        )

    @_async_mode_handler
    def get_group_members(self, group: Union[GroupId,str]) -> Sequence[Member]:
        """
        """
        return self._request_something(
            "GET",
            "{SERVER}/groups/{group_ref}/members",
            lambda list_: [Member(m) for m in list_],
            200,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
        )

    @_async_mode_handler
    def get_system_settings(self, system: Union[SystemId,str,int,None]=None) -> SystemSettings:
        """
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/settings",
            SystemSettings,
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            system=system,
        )

    @_async_mode_handler
    def get_system_guild_settings(self, guild_id: int) -> SystemGuildSettings:
        """Get the system guild settings of the client's system.

        Note:
            This requires your authorization token.
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/@me/guilds/{guild_id}",
            SystemGuildSettings,
            200,
            GUILD_ERROR_CODE_LOOKUP,
            guild_id=guild_id,
        )

    @_async_mode_handler
    def get_member_guild_settings(self, member: Union[MemberId,str], guild_id: int) -> MemberGuildSettings:
        """Get the member guild settings of a member.
        """
        error_lookups = GENERIC_ERROR_CODE_LOOKUP | {403: NotOwnMember}
        return self._request_something(
            "GET",
            "{SERVER}/members/{member_ref}/guilds/{guild_id}",
            MemberGuildSettings,
            200,
            error_lookups,
            member=member,
            guild_id=guild_id,
        )

    # 
    #  delete
    # 

    @_async_mode_handler
    def delete_member(self, member: Union[MemberId,str]) -> None:
        """
        """
        return self._request_something(
            "DELETE",
            "{SERVER}/members/{member_ref}",
            lambda x: None,
            204,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
        )

    @_async_mode_handler
    def delete_group(self, group: Union[GroupId,Group]) -> None:
        """
        """
        if isinstance(group, Group): group = group.id
        return self._request_something(
            "DELETE",
            "{SERVER}/groups/{group_ref}",
            lambda x: None,
            204,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
        )

    @_async_mode_handler
    def delete_switch(self, switch: Union[SwitchId,Switch]) -> None:
        """
        """
        if isinstance(switch, Switch): switch = switch.id
        return self._request_something(
            "DELETE",
            "{SERVER}/systems/@me/switches/{switch_ref}",
            lambda x: None,
            204,
            SWITCH_ERROR_CODE_LOOKUP,
            switch=switch,
        )

    # 
    #  add, remove, set
    # 

    def _gather_args(self, args, context) -> Sequence[str]:
        ALLOWED = {
            "groups": {
                Group: lambda g: g.id.uuid,
                GroupId: lambda gid: gid.uuid,
            },
            "members": {
                Member: lambda m: m.id.uuid,
                MemberId: lambda mid: mid.uuid,
            }
        }
        arg_list = []
        for arg in args:
            for allowed_type in ALLOWED[context]:
                if isinstance(arg, allowed_type):
                    func = ALLOWED[context][allowed_type]
                    arg_list.append(func(arg))
                    break
            else:
                allowed_types = ", ".join([c.__name__ for c in ALLOWED[context].keys()])
                msg = (
                    f"{context} must be of any of these types: {allowed_types}. "
                    f"Encountered type {type(group)!r} ({group!r})."
                )
                raise ValueError(msg)
        return arg_list

    @_async_mode_handler
    def add_member_to_groups(self, member: Union[MemberId,str], groups) -> None:
        """Add a member to each group in a given list of groups.

        Not to be confused with `Client.add_members_to_group`.

        Arguments:
            member: The member to add to the groups.
            groups (Sequence[Union[GroupId,Group]]): The groups to add the member to.
        """
        group_list = self._gather_args(groups, "groups")
        return self._request_something(
            "POST",
            "{SERVER}/members/{member_ref}/groups/add",
            lambda x: None,
            204,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
            payload=group_list,
        )

    @_async_mode_handler
    def remove_member_from_groups(self, member: Union[MemberId,str], groups) -> None:
        """Remove a member from each group in a given list of groups.

        Not to be confused with `Client.remove_members_from_group`.

        Tip:
            If you want to remove *all* groups from a member, consider using
            `Client.set_member_groups` with no groups.

        Arguments:
            member: The member to remove from the groups.
            groups (Sequence[Union[GroupId,Group]]): The groups to remove the member from.
        """
        group_list = self._gather_args(groups, "groups")
        return self._request_something(
            "POST",
            "{SERVER}/members/{member_ref}/groups/remove",
            lambda x: None,
            204,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
            payload=group_list,
        )

    @_async_mode_handler
    def set_member_groups(self, member: Union[MemberId,str], groups) -> None:
        """Explicitly set which groups a member belongs to.

        Not to be confused with `Client.set_group_members`.

        An empty list is accepted, effectively removing the member from any & all groups.

        Arguments:
            member: The member for which to set the groups.
            groups (Sequence[Union[GroupId,Group]]): The groups to assign to the member.
        """
        group_list = self._gather_args(groups, "groups")
        return self._request_something(
            "POST",
            "{SERVER}/members/{member_ref}/groups/overwrite",
            lambda x: None,
            204,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
            payload=group_list,
        )

    @_async_mode_handler
    def add_members_to_group(self, group: Union[GroupId,Group], members) -> None:
        """Add members to a group.

        Not to be confused with `Client.add_member_to_groups`.

        Arguments:
            group: The group to add the members to.
            members (Sequence[Union[Member,MemberId]]): The members to add to the group.
        """
        member_list = self._gather_args(members, "members")
        return self._request_something(
            "POST",
            "{SERVER}/groups/{group_ref}/members/add",
            lambda x: None,
            204,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
            payload=member_list,
        )

    @_async_mode_handler
    def remove_members_from_group(self, group: Union[GroupId,Group], members) -> None:
        """Remove members from a group.

        Not to be confused with `Client.remove_member_from_groups`.

        Tip:
            If you want to remove *all* members from a group, consider using
            `Client.set_group_members` with no members.

        Arguments:
            group: The group to remove the members from.
            members (Sequence[Union[Member,MemberId]]): The members to remove from the group.
        """
        member_list = self._gather_args(members, "members")
        return self._request_something(
            "POST",
            "{SERVER}/groups/{group_ref}/members/remove",
            lambda x: None,
            204,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
            payload=member_list,
        )

    @_async_mode_handler
    def set_group_members(self, group: Union[GroupId,Group], members) -> None:
        """Remove members from a group.

        Not to be confused with `Client.set_member_groups`.

        An empty list is accepted, effectively removing all members from a group.

        Arguments:
            group: The group to remove the members from.
            members (Sequence[Union[Member,MemberId]]): The members to assign to the group.
        """
        member_list = self._gather_args(members, "members")
        return self._request_something(
            "POST",
            "{SERVER}/groups/{group_ref}/members/overwrite",
            lambda x: None,
            204,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
            payload=member_list,
        )

    # 
    #  update (patches)
    # 

    def _check_update_keys(self, context, kwargs, allowed, require_at_least_one_arg=True):
        if require_at_least_one_arg and not kwargs:
            msg = f"{context} expects at least 1 keyword argument"
            raise TypeError(msg)
        for key in kwargs:
            if key not in allowed:
                msg = f"{context} got an unexpected keyword argument {key!r}"
                raise TypeError(msg)

    @_async_mode_handler
    def update_system(self, **kwargs) -> System:
        """Update your system.

        Keyword arguments:
            name
            description
            tag
            pronouns
            avatar_url
            banner
            color
            description_privacy
            pronoun_privacy
            member_list_privacy
            group_list_privacy
            front_privacy
            front_history_privacy
        """
        self._check_update_keys("update_system()", kwargs, _PATCHABLE_SYSTEM_KEYS)
        payload = {}
        privacies = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_SYSTEM_KEYS[key](value)
            if key in _PRIVACY_ASSOCIATED_KEYS:
                privacies[key] = json_value
            else:
                payload[key] = json_value
        if privacies: payload["privacy"] = privacies
        return self._request_something(
            "PATCH",
            "{SERVER}/systems/@me",
            System,
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            payload=payload,
        )

    @_async_mode_handler
    def update_system_settings(self, **kwargs) -> SystemSettings:
        """Update your system settings.

        Keyword arguments:
            timezone
            pings_enabled
            latch_timeout
            member_default_private
            group_default_private
            show_private_info
        """
        self._check_update_keys("update_system_settings()",
            kwargs, _PATCHABLE_SYSTEM_SETTINGS_KEYS)
        payload = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_SYSTEM_SETTINGS_KEYS[key](value)
            payload[key] = json_value
        return self._request_something(
            "PATCH",
            "{SERVER}/systems/@me/settings",
            SystemSettings,
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            payload=payload
        )

    @_async_mode_handler
    def update_system_guild_settings(self, guild_id: int, **kwargs) -> SystemGuildSettings:
        """Update your system guild settings.

        Arguments:
            guild_id

        Keyword arguments:
            proxying_enabled
            tag
            tag_enabled
        """
        self._check_update_keys("update_system_guild_settings()",
            kwargs, _PATCHABLE_SYSTEM_GUILD_SETTINGS_KEYS)
        payload = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_SYSTEM_GUILD_SETTINGS_KEYS[key](value)
            payload[key] = json_value
        return self._request_something(
            "PATCH",
            "{SERVER}/systems/@me/guilds/{guild_id}",
            SystemGuildSettings,
            200,
            GUILD_ERROR_CODE_LOOKUP,
            guild_id=guild_id,
            payload=payload
        )

    @_async_mode_handler
    def update_member(self, member: Union[MemberId,Member], **kwargs) -> Member:
        """Update a system member
        """
        if isinstance(member, Member): member = member.id
        self._check_update_keys("update_member()", kwargs, _PATCHABLE_MEMBER_KEYS)
        payload = {}
        privacies = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_MEMBER_KEYS[key](value)
            if key in _PRIVACY_ASSOCIATED_KEYS:
                privacies[key] = json_value
            else:
                payload[key] = json_value
        if privacies: payload["privacy"] = privacies
        return self._request_something(
            "PATCH",
            "{SERVER}/members/{member_ref}",
            Member,
            200,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
            payload=payload,
        )

    @_async_mode_handler
    def update_member_guild_settings(self,
        member: Union[Member,MemberId], guild_id: int, **kwargs) -> MemberGuildSettings:
        """Update your member guild settings.

        Arguments:
            member
            guild_id

        Keyword arguments:
            proxying_enabled
            tag
            tag_enabled
        """
        self._check_update_keys("update_member_guild_settings()",
            kwargs, _PATCHABLE_MEMBER_GUILD_SETTINGS_KEYS)
        payload = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_MEMBER_GUILD_SETTINGS_KEYS[key](value)
            payload[key] = json_value
        if isinstance(member, Member): member = member.id
        error_lookups = GENERIC_ERROR_CODE_LOOKUP | {403: NotOwnMember}
        return self._request_something(
            "PATCH",
            "{SERVER}/members/{member_ref}/guilds/{guild_id}",
            MemberGuildSettings,
            200,
            error_lookups,
            member=member,
            guild_id=guild_id,
            payload=payload
        )

    @_async_mode_handler
    def update_group(self, group: Union[GroupId,Group], **kwargs) -> Group:
        """
        """
        self._check_update_keys("update_group()", kwargs, _PATCHABLE_GROUP_KEYS)
        payload = {}
        privacies = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_GROUP_KEYS[key](value)
            if key in _PRIVACY_ASSOCIATED_KEYS:
                privacies[key] = json_value
            else:
                payload[key] = json_value
        if privacies: payload["privacy"] = privacies
        if isinstance(group, Group): group = group.id
        return self._request_something(
            "PATCH",
            "{SERVER}/groups/{group_ref}",
            Group,
            200,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
            payload=payload,
        )

    # note: two endpoints per this method
    @_async_mode_handler
    def update_switch(self, switch: Union[SwitchId,Switch], **kwargs) -> Switch:
        """Update a logged switch.

        Arguments:
            switch

        Keyword arguments:
            timestamp: When the switch happened.
            members (Sequence[Union[Member,MemberId]]): The list of member IDs.
        """
        self._check_update_keys("update_switch()", kwargs, _PATCHABLE_SWITCH_KEYS)
        awaitables = []
        if "members" in kwargs:
            members = _PATCHABLE_SWITCH_KEYS["members"](kwargs["members"])
            awaitable = self._request_something(
                "PATCH",
                "{SERVER}/systems/@me/switches/{switch_ref}/members",
                Switch,
                200,
                SWITCH_ERROR_CODE_LOOKUP,
                switch=switch,
                payload=members,
            )
            awaitables.append(awaitable)
        if "timestamp" in kwargs:
            timestamp = _PATCHABLE_SWITCH_KEYS["timestamp"](kwargs["timestamp"])
            awaitable = self._request_something(
                "PATCH",
                "{SERVER}/systems/@me/switches/{switch_ref}",
                Switch,
                200,
                SWITCH_ERROR_CODE_LOOKUP,
                switch=switch,
                payload={"timestamp": timestamp},
            )
            awaitables.append(awaitable)
        
        async def send_request(awaitables):
            results = []
            for a in awaitables:
                results.append(await a) # purposefully block

            return results[-1]

        return send_request(awaitables)

    @_async_mode_handler
    def new_member(self, name: str, **kwargs) -> Member:
        """Create a new member in your system.

        Arguments:
            name: The name of the new member. 100 character limit.

        Keyword args:
            display_name
            color
            birthday
            pronouns
            avatar_url
            banner
            description
            proxy_tags
            keep_proxy
            visibility
            name_privacy
            description_privacy
            birthday_privacy
            pronoun_privacy
            avatar_privacy
            metadata_privacy
        """
        name = _PATCHABLE_MEMBER_KEYS["name"](name)
        self._check_update_keys("new_member()", kwargs, _PATCHABLE_MEMBER_KEYS,
            require_at_least_one_arg)
        payload = {"name": name}
        privacies = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_MEMBER_KEYS[key](value)
            if key in _PRIVACY_ASSOCIATED_KEYS:
                privacies[key] = json_value
            else:
                payload[key] = json_value
        if privacies: payload["privacy"] = privacies
        return self._request_something(
            "POST",
            "{SERVER}/members",
            Member,
            200,
            GENERIC_ERROR_CODE_LOOKUP,
            payload=payload,
        )

    @_async_mode_handler
    def new_group(self, name: str, **kwargs) -> Group:
        """Create a new group

        Arguments:
            name: Name of the group. 100 character limit.

        Keyword args:
            display_name
            description
            icon
            banner
            color
            name_privacy
            description_privacy
            icon_privacy
            list_privacy
            metadata_privacy
            visibility
        """
        name = _PATCHABLE_GROUP_KEYS["name"](name)
        self._check_update_keys("new_group()", kwargs, _PATCHABLE_GROUP_KEYS,
            require_at_least_one_arg=False)
        payload = {"name": name}
        privacies = {}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_GROUP_KEYS[key](value)
            if key in _PRIVACY_ASSOCIATED_KEYS:
                privacies[key] = json_value
            else:
                payload[key] = json_value
        if privacies: payload["privacy"] = privacies
        return self._request_something(
            "POST",
            "{SERVER}/groups",
            Group,
            200,
            GENERIC_ERROR_CODE_LOOKUP,
            payload=payload,
        )

    @_async_mode_handler
    def new_switch(self, members, timestamp=None) -> Switch:
        """Log a new switch

        Arguments:
            members: List of members in this switch.

        Keyword args:
            timestamp: Defaults to "now".
        """
        payload = {}
        payload["members"] = _PATCHABLE_SWITCH_KEYS["members"](members)
        if timestamp is not None:
            payload["timestamp"] = _PATCHABLE_SWITCH_KEYS["timestamp"](timestamp)
        return self._request_something(
            "POST",
            "{SERVER}/systems/{system_ref}/switches",
            Switch,
            200,
            GENERIC_ERROR_CODE_LOOKUP,
            payload=payload,
        )
