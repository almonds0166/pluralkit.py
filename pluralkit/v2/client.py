
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Callable,
    AsyncGenerator, Awaitable,
)
import datetime
import asyncio
from http.client import responses as RESPONSE_CODES
from functools import wraps

import httpx

from .models import (
    Model,
    AutoproxyMode,
    MemberId, SystemId, GroupId, SwitchId,
    Member, System, Group, Switch, Message,
    MemberGuildSettings, SystemGuildSettings,
    SystemSettings, AutoproxySettings,
    Timestamp, Privacy,
    _PATCHABLE_SYSTEM_KEYS,
    _PATCHABLE_MEMBER_KEYS,
    _PATCHABLE_GROUP_KEYS,
    _PATCHABLE_SWITCH_KEYS,
    _PATCHABLE_AUTOPROXY_SETTINGS_KEYS,
    _PATCHABLE_SYSTEM_SETTINGS_KEYS,
    _PATCHABLE_SYSTEM_GUILD_SETTINGS_KEYS,
    _PATCHABLE_MEMBER_GUILD_SETTINGS_KEYS,
    _PRIVACY_ASSOCIATED_KEYS,
)
from .errors import (
    PluralKitException,
    HTTPError,
    GenericBadRequest,
    NotFound,
    SystemNotFound,
    MemberNotFound,
    GroupNotFound,
    SwitchNotFound,
    MessageNotFound,
    GuildNotFound,
    Unauthorized,
    NotOwnSystem,
    NotOwnMember,
    NotOwnGroup,
    GENERIC_ERROR_CODE_LOOKUP,
    SYSTEM_ERROR_CODE_LOOKUP,
    MEMBER_ERROR_CODE_LOOKUP,
    GROUP_ERROR_CODE_LOOKUP,
    MESSAGE_ERROR_CODE_LOOKUP,
    SWITCH_ERROR_CODE_LOOKUP,
    GUILD_ERROR_CODE_LOOKUP,
)

SERVER = "https://api.pluralkit.me/v2"

async def aiter(generator: Awaitable) -> AsyncGenerator:
    """For conversion of any awaitables to async generators/sequences

    Applies to async_mode=True Sequence methods
    """
    items = await generator
    for item in items:
        yield item
        await asyncio.sleep(0)

class Client:
    """Represents a client that interacts with the PluralKit API.

    Args:
        token: The PluralKit `authorization token`_, from the ``pk;token`` command.

    Keyword args:
        async_mode: Whether the client runs asynchronously (``True``, default) or not (``False``).
        user_agent: The User-Agent header to use with the API.
        loop: The `asyncio` event loop to use (if ``async_mode=True``), default is the current
            event loop.

    Attributes:
        token: The client's PluralKit authorization token.
        async_mode: Whether the client runs asynchronously (``True``) or not (``False``).
        headers: The headers the client uses to communicate with the API.

    .. _`authorization token`: https://pluralkit.me/api/#authentication
    """
    def __init__(self, token: Optional[str]=None, *,
        async_mode: bool=True,
        user_agent: Optional[str]=None,
        loop: asyncio.AbstractEventLoop=None,
    ):
        # core factors
        self.async_mode = async_mode
        self.loop = loop
        self.id = None
        self._token = token

        # initialize rate limit handling
        self._rate_limit = 2 # default is 2 requests per second
        self._rate_limit_remaining = 0
        self._rate_limit_reset_time = datetime.datetime.now()

        # set up headers
        self.headers = {}
        if user_agent: self.headers["User-Agent"] = user_agent
        if token: self.headers["Authorization"] = token

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, new_token):
        self._token = new_token
        if new_token is None:
            del self.headers["Authorization"]
        else:
            self.headers["Authorization"] = new_token

    # ==========================
    #  abstract request methods
    # ==========================

    async def _respect_rate_limit(self):
        """Respects the rate limit by waiting if necessary."""
        if self._rate_limit_remaining == 0:
            now = datetime.datetime.now()
            if self._rate_limit_reset_time < now:
                self._rate_limit_remaining = self._rate_limit
            else:
                await asyncio.sleep((self._rate_limit_reset_time - now).total_seconds())
                self._rate_limit_remaining = self._rate_limit
            self._rate_limit_reset_time = now + datetime.timedelta(seconds=1) # until otherwise specified
 
    def _update_rate_limits(self, headers):
        """Updates the rate limits based on the returned headers."""
        if "X-RateLimit-Limit" in headers:
            self._rate_limit = int(headers["X-RateLimit-Limit"])
        if "X-RateLimit-Remaining" in headers:
            self._rate_limit_remaining = int(headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in headers:
            timestamp = float(headers["X-RateLimit-Reset"]) / 1000.0
            self._rate_limit_reset_time = datetime.datetime.fromtimestamp(timestamp)
            #print("reset at:", self._rate_limit_reset_time - datetime.datetime.now())

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
        # optional payloads
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

        # respect rate limit
        await self._respect_rate_limit()

        # make the request
        async with httpx.AsyncClient(headers=self.headers) as session:
            request_func = getattr(session, kind.lower())
            kwargs = {}
            if params is not None: kwargs["params"] = params
            if payload is not None: kwargs["json"] = payload
            response = await request_func(url, **kwargs)

            # update rate limit mechanics
            headers = response.headers
            self._update_rate_limits(headers)

            # analyze returned info
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
                return_type = wrapped_function.__annotations__.get("return")
                try:
                    is_generator = return_type is not None and return_type._name == Sequence._name
                except AttributeError:
                    is_generator = False
                return aiter(awaitable) if is_generator else awaitable
            else:
                loop = instance.loop if instance.loop is not None else asyncio.get_event_loop()
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
    def get_system(self, system: Union[SystemId,int,None]=None) -> System:
        """Get a system by its reference ID.

        Args:
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authorization token.
        """
        if isinstance(system, System): system = system.id
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}",
            System,
            200,
            SYSTEM_ERROR_CODE_LOOKUP,
            system=system,
        )

    @_async_mode_handler
    def get_member(self, member: Union[MemberId,str]) -> Member:
        """Get a member by its reference ID.

        Args:
            member: Member reference (`MemberId`).
        """
        return self._request_something(
            "GET",
            "{SERVER}/members/{member_ref}",
            Member,
            200,
            MEMBER_ERROR_CODE_LOOKUP,
            member=member,
        )

    @_async_mode_handler
    def get_group(self, group: Union[GroupId,str]) -> Group:
        """Get a group by its reference ID.

        Args:
            group: Group reference (`GroupId`).
        """
        return self._request_something(
            "GET",
            "{SERVER}/groups/{group_ref}",
            Group,
            200,
            GROUP_ERROR_CODE_LOOKUP,
            group=group,
        )

    @_async_mode_handler
    def get_message(self, message: int) -> Message:
        """Get information about a proxied message.

        Args:
            message: The Discord ID of a proxied message, or the Discord ID of the message that
                sent the proxy.
        """
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
    ) -> Sequence[Switch]:
        """Get list of system switches.

        Returns at most 100 switches. To get additional, specify the ``before`` parameter.

        Note:
            Because this is a batch API call, the `Switch` objects returned by this method have
            `MemberId` objects for `Switch.members` rather than full `Member` objects.

        Hint:
            This method returns an async generator when the `Client` is in asynchronous mode
            (and with ``async_mode=False``, it returns a list), so use the ``async for`` syntax instead of
            ``await``: ::

                async for switch in client.get_switches(...):
                    ...

            If you find a list preferable to an async generator, use a list comprehension such
            as ::

                switches = [s async for s in client.get_switches(...)]
                ...

        Args:
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authoirzation token.

        Keyword args:
            before: Timestamp before which to get latest switches from. Default is ``None``
                ("now").
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

        Hint:
            This method returns an async generator when the `Client` is in asynchronous mode
            (and with ``async_mode=False``, it returns a list), so use the ``async for`` syntax instead of
            ``await``: ::

                async for member in client.get_fronters(...):
                    ...

            If you find a list preferable to an async generator, use a list comprehension such
            as ::

                fronters = [m async for m in client.get_fronters(...)]
                ...

        Args:
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authoirzation token.
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
    def get_switch(self, switch: Union[SwitchId,str], system: Union[SystemId,int,None]=None
    ) -> Switch:
        """Get switch information by its reference ID.

        Args:
            switch: Switch reference (`SwitchId`).
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
        """Get the list of a system's members.

        Hint:
            This method returns an async generator when the `Client` is in asynchronous mode
            (and with ``async_mode=False``, it returns a list), so use the ``async for`` syntax instead of
            ``await``. For example: ::

                async for member in client.get_members(...):
                    ...

            If you find a list preferable to an async generator, use a list comprehension such
            as ::

                members = [m async for m in client.get_members(...)]
                ...

        Args:
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authoirzation token.
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
        """Get the list of groups a member is a part of.

        Hint:
            This method returns an async generator when the `Client` is in asynchronous mode
            (and with ``async_mode=False``, it returns a list), so use the ``async for`` syntax instead of
            ``await``. For example: ::

                async for group in client.get_member_groups(...):
                    ...

            If you find a list preferable to an async generator, use a list comprehension such
            as ::

                groups = [g async for g in client.get_member_groups(...)]
                ...

        Args:
            member: Member reference (`MemberId`).
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
    def get_groups(self, system: Union[SystemId,int,None]=None) -> Sequence[Group]:
        """Get the list of a system's groups.

        Hint:
            This method returns an async generator when the `Client` is in asynchronous mode
            (and with ``async_mode=False``, it returns a list), so use the ``async for`` syntax instead of
            ``await``. For example: ::

                async for group in client.get_groups(...):
                    ...

            If you find a list preferable to an async generator, use a list comprehension such
            as ::

                groups = [g async for g in client.get_groups(...)]
                ...

        Args:
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authoirzation token.
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
        """Get the list of members of a group.

        Hint:
            This method returns an async generator when the `Client` is in asynchronous mode
            (and with ``async_mode=False``, it returns a list), so use the ``async for`` syntax instead of
            ``await``. For example: ::

                async for member in client.get_group_members(...):
                    ...

            If you find a list preferable to an async generator, use a list comprehension such
            as ::

                members = [m async for m in client.get_group_members(...)]
                ...

        Args:
            group: Group reference (`GroupId`).
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
        """Get a system's settings (e.g. defaults, timezone, limits).

        Args:
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authoirzation token.
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
    def get_autoproxy_settings(self, guild_id: int) -> AutoproxySettings:
        """Get the autoproxy settings of your system.

        Args:
            guild_id: Discord guild ID.
        """
        return self._request_something(
            "GET",
            "{SERVER}/systems/@me/autoproxy",
            AutoproxySettings,
            200,
            GENERIC_ERROR_CODE_LOOKUP,
            params={"guild_id": guild_id},
        )

    @_async_mode_handler
    def get_system_guild_settings(self, guild_id: int, system: Union[SystemId,int,None]=None) \
    -> SystemGuildSettings:
        """Get the guild settings of a system.

        Args:
            guild_id: Discord guild ID.
            system: System reference; a system's ID (`SystemId`) or the ID of a Discord account
                linked to the system. Default is ``None``, for the system corresponding to the
                client's authoirzation token.
        """
        error_lookups = GENERIC_ERROR_CODE_LOOKUP | {403: NotOwnSystem}
        return self._request_something(
            "GET",
            "{SERVER}/systems/{system_ref}/guilds/{guild_id}",
            SystemGuildSettings,
            200,
            error_lookups,
            guild_id=guild_id,
            system=system,
        )

    @_async_mode_handler
    def get_member_guild_settings(self, guild_id: int, member: Union[MemberId,str]) \
    -> MemberGuildSettings:
        """Get the guild settings of a member.

        Args:
            guild_id: Discord guild ID.
            member: Member reference (`MemberId`).
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
        """Remove a member from your system.

        Args:
            member: Member reference (`MemberId`).
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
        """Remove a group from your system.

        Args:
            group: Group reference (`GroupId`).
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
        """Remove a logged switch from your system.

        Args:
            switch: Switch reference (`SwitchId`).
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
    def add_member_groups(self, member: Union[MemberId,str], groups) -> None:
        """Add a member to each group in a given list of groups.

        Not to be confused with `Client.add_group_members`.

        Args:
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
    def remove_member_groups(self, member: Union[MemberId,str], groups) -> None:
        """Remove a member from each group in a given list of groups.

        Not to be confused with `Client.remove_group_members`.

        Tip:
            If you want to remove *all* groups from a member, consider using
            `Client.set_member_groups` with no groups.

        Args:
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

        Args:
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
    def add_group_members(self, group: Union[GroupId,Group], members) -> None:
        """Add members to a group.

        Not to be confused with `Client.add_member_groups`.

        Args:
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
    def remove_group_members(self, group: Union[GroupId,Group], members) -> None:
        """Remove members from a group.

        Not to be confused with `Client.remove_member_groups`.

        Tip:
            If you want to remove *all* members from a group, consider using
            `Client.set_group_members` with no members.

        Args:
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

        Args:
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

        Keyword args:
            name (str): System name (100 character limit).
            description (Optional[str]): System description (1,000 character limit). ``None`` to
                clear.
            tag (str): System tag (79 character limit).
            pronouns (Optional[str]): System pronouns (100 character limit). ``None`` to clear.
            avatar_url (Optional[str]): System avatar url (256 character limite). ``None`` to
                clear.
            banner (Optional[str]): System banner url (256 character limite). ``None`` to clear.
            color (Color): System color.
            description_privacy (Optional[Privacy]): System description privacy. ``None`` to reset
                (to public).
            pronoun_privacy (Optional[Privacy]): System pronoun privacy. ``None`` to reset (to
                public).
            member_list_privacy (Optional[Privacy]): System member list privacy. ``None`` to reset
                (to public).
            group_list_privacy (Optional[Privacy]): System group list privacy. ``None`` to reset
                (to public).
            front_privacy (Optional[Privacy]): System current fronter privacy. ``None`` to reset
                (to public).
            front_history_privacy (Optional[Privacy]): System front history privacy. ``None`` to
                reset (to public).
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

        Keyword args:
            timezone (Timezone): System timezone. ``None`` resets to UTC.
            pings_enabled (bool): Whether other users are able to ping your system (with a 🔔
                reaction).
            latch_timeout (Optional[int]): For autoproxy latch mode, this sets the amount of time
                elapsed since the last proxied message in the server that resets the latch.
                ``None`` resets to default (6 hr).
            member_default_private (bool): Whether member privacy is automatically set to private for new members.
                Applies only to new members created by the bot and *not* created by the PluralKit API directly.
            group_default_private (bool): Whether group privacy is automatically set to private for new groups. Applies
                only to new groups created by the bot and *not* created by the PluralKit API directly.
            show_private_info (bool): Whether the bot shows the system's own private information without a ``-private``
                flag.
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
    def update_autoproxy_settings(self, guild_id: int, autoproxy_mode: AutoproxyMode, **kwargs) -> AutoproxySettings:
        """Update your system's autoproxy settings.

        Args:
            guild_id: Discord guild ID.
            autoproxy_mode (AutoproxyMode): The autoproxy mode to use for this Discord server.

        Keyword args:
            autoproxy_member (Union[MemberId,Member,None]): The member to autoproxy, when autoproxy
                mode is set to `AutoproxyMode.MEMBER`.
        """
        self._check_update_keys("update_autoproxy_settings()",
            kwargs, _PATCHABLE_AUTOPROXY_SETTINGS_KEYS, require_at_least_one_arg=False)
        autoproxy_mode = AutoproxyMode(autoproxy_mode)
        payload = {"autoproxy_mode": autoproxy_mode.json()}
        for key, value in kwargs.items():
            json_value = _PATCHABLE_AUTOPROXY_SETTINGS_KEYS[key](value)
            payload[key] = json_value
        # API quirk?
        if autoproxy_mode == AutoproxyMode.FRONT and "autoproxy_member" in kwargs:
            kwargs["autoproxy_member"] = None
        return self._request_something(
            "PATCH",
            "{SERVER}/systems/@me/autoproxy",
            AutoproxySettings,
            200,
            GUILD_ERROR_CODE_LOOKUP,
            payload=payload,
            params={"guild_id": guild_id},
        )

    @_async_mode_handler
    def update_system_guild_settings(self, guild_id: int, **kwargs) -> SystemGuildSettings:
        """Update your system's guild settings.

        Args:
            guild_id: Discord guild ID.

        Keyword args:
            proxying_enabled (bool): Whether the system can proxy messages in this guild.
            tag (Optional[str]): System tag in this guild (79 character limit). Use ``None`` to
                clear.
            tag_enabled (bool): Whether the system tag is enabled for this guild.
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
        """Update a system member.

        Args:
            member: Member reference (`MemberId`).

        Keyword args:
            name (str): Member name (100 character limit).
            display_name (Optional[str]): Member display name (100 character limit). ``None`` to
                clear.
            color (Color): Member color.
            birthday (Optional[Birthday]): Member birthday. ``None`` to clear.
            pronouns (Optional[str]): Member pronouns (100 character limit). ``None`` to clear.
            avatar_url (Optional[str]): Member avatar url (256 character limit). ``None`` to clear.
            banner (Optional[str]): Member banner url (256 character limit). ``None`` to clear.
            description (Optional[str]): Member description (1,000 character limit). ``None`` to
                clear.
            proxy_tags (Union[ProxyTag,ProxyTags,Sequence[ProxyTag]]): Member proxy tags. Use an
                empty list to remove the member's set of proxy tags.
            keep_proxy (bool): Whether to keep the proxy prefix and/or suffix for this member's
                proxied messages.
            visibility (Optional[Privacy]): Whether this member is visible to others (i.e. in
                member lists). ``None`` to reset to default (public).
            name_privacy (Optional[Privacy]): Whether the member name is visible to others or only
                the display name. ``None`` to reset to default (public).
            description_privacy (Optional[Privacy]): Whether the member description is visible to
                others. ``None`` to reset to default (public).
            birthday_privacy (Optional[Privacy]): Whether the member birthday is visible to others.
                ``None`` to reset to default (public).
            pronoun_privacy (Optional[Privacy]): Whether the member pronouns are visible to others.
                ``None`` to reset to default (public).
            avatar_privacy (Optional[Privacy]): Whether the member avatar is visible to others.
                ``None`` to reset to default (public).
            metadata_privacy (Optional[Privacy]): Whether the member's metadata (i.e. created
                timestamp, message count) is visible to others. ``None`` to reset to default
                (public).
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
        guild_id: int, member: Union[Member,MemberId], **kwargs) -> MemberGuildSettings:
        """Update a member's guild settings.

        Args:
            guild_id: Discord guild ID.
            member: Member reference (`MemberId`).

        Keyword args:
            display_name (Optional[str]): Member display name (100 character limit). ``None`` to
                clear.
            avatar_url (Optional[str]): Member avatar url (256 character limit). ``None`` to clear.
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
        """Update a group's settings.

        Args:
            group: Group reference (`GroupId`).

        Keyword args:
            name (str): Group name (100 character limit).
            display_name (Optional[str]): Group display name (100 character limit). ``None`` to
                clear.
            description (Optional[str]): Group description (1,000 character limit). ``None`` to
                clear.
            icon (Optional[str]): Group icon url (256 character limit). ``None`` to clear.
            banner (Optional[str]): Group banner url (256 character limit). ``None`` to clear.
            color (Color): Group color.
            name_privacy (Optional[Privacy]): Whether the group name is visible to others or only
                the display name. ``None`` to reset to default (public).
            description_privacy (Optional[Privacy]): Whether the group description is visilbe to
                others. ``None`` to reset to default (public).
            icon_privacy (Optional[Privacy]): Whether the group icon is visible to others. ``None``
                to reset to default (public).
            list_privacy (Optional[Privacy]): Whether the group member list is visible to others.
                ``None`` to reset to default (public).
            metadata_privacy (Optional[Privacy]): Whether the groups's metadata (i.e. created
                timestamp) is visible to others. ``None`` to reset to default (public).
            visibility (Optional[Privacy]): Whether this group is visible to others (i.e. in group
                lists). ``None`` to reset to default (public).
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

        Args:
            switch: Switch reference (`SwitchId`).

        Keyword args:
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
                                        # to return only most recent Switch model
            return results[-1]

        return send_request(awaitables)

    @_async_mode_handler
    def new_member(self, name: str, **kwargs) -> Member:
        """Create a new member in your system.

        Args:
            name: The name of the new member. 100 character limit.

        Keyword args:
            display_name (str): Member display name (100 character limit).
            color (Color): Member color.
            birthday (Birthday): Member birthday.
            pronouns (str): Member pronouns (100 character limit).
            avatar_url (str): Member avatar url (256 character limit).
            banner (str): Member banner url (256 character limit).
            description (str): Member description (1,000 character limit).
            proxy_tags (Union[ProxyTag,ProxyTags,Sequence[ProxyTag]]): Member proxy tags.
            keep_proxy (bool): Whether to keep the proxy prefix and/or suffix for this member's
                proxied messages.
            visibility (Privacy): Whether this member is visible to others (i.e. in member lists).
                Default is public.
            name_privacy (Privacy): Whether the member name is visible to others or only the display
                name. Default is public.
            description_privacy (Privacy): Whether the member description is visible to others.
                Default is public.
            birthday_privacy (Privacy): Whether the member birthday is visible to others. Default
                is public.
            pronoun_privacy (Privacy): Whether the member pronouns are visible to others. Default
                is public.
            avatar_privacy (Privacy): Whether the member avatar is visible to others. Default is
                public.
            metadata_privacy (Privacy): Whether the member's metadata (i.e. created timestamp,
                message count) is visible to others. Default is public.
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

        Args:
            name: Name of the group. 100 character limit.

        Keyword args:
            display_name (str): Group display name (100 character limit).
            description (str): Group description (1,000 character limit).
            icon (str): Group icon url (256 character limit).
            banner (str): Group banner url (256 character limit).
            color (Color): Group color.
            name_privacy (Privacy): Whether the group name is visible to others or only the display
                name. Default is public.
            description_privacy (Privacy): Whether the group description is visilbe to others.
                Default is public.
            icon_privacy (Privacy): Whether the group icon is visible to others. Default is public.
            list_privacy (Privacy): Whether the group member list is visible to others. Default is
                public.
            metadata_privacy (Privacy): Whether the groups's metadata (i.e. created timestamp) is
                visible to others. Default is public.
            visibility (Privacy): Whether this group is visible to others (i.e. in group lists).
                Default is public.
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
        """Log a new switch.

        Args:
            members (Sequence[Union[MemberId,Member]]): List of members in this switch.

        Keyword args:
            timestamp (Timestamp): Time of switch. ``None`` for "now" (default).
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
