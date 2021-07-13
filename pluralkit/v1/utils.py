
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Awaitable, AsyncGenerator, Coroutine,
)
import datetime
from http.client import responses as RESPONSE_CODES

import httpx
import colour
import pytz

from .models import Birthday, ProxyTag, Privacy, Timestamp, Timezone, Color
from .errors import *

MEMBER_ATTRS = (
    "name", 
    "display_name", 
    "description", 
    "pronouns", 
    "color", 
    "avatar_url", 
    "birthday", 
    "proxy_tags", 
    "keep_proxy", 
    "visibility", 
    "name_privacy", 
    "description_privacy", 
    "avatar_privacy", 
    "pronoun_privacy",
    "metadata_privacy",
    "birthday_privacy"
)

SYSTEM_ATTRS = (
    "name",
    "description",
    "tag",
    "avatar_url",
    "tz",
    "description_privacy",
    "member_list_privacy",
    "front_privacy",
    "front_history_privacy"
)

async def flatten(x: AsyncGenerator[Any,None]) -> List[Any]:
    flattened = []
    async for item in x:
        flattened.append(item)
    return flattened

async def member_value(kwargs, key, value):
    """Prepares the kwargs given to `~v1.client.Client` methods for PluralKit's API, for internal
    use.
    """
    if not key in MEMBER_ATTRS:
        raise InvalidKwarg(key)
    if key == "color":
        if value is not None:
            kwargs[key] = Color.parse(value).hex_l[1:]
    elif key == "birthday":
        if isinstance(value, datetime.date):
            kwargs[key] = value.strftime(r"%Y-%m-%d")
        elif isinstance(value, str):
            try:
                datetime.datetime.strptime(value, r"%Y-%m-%d")
            except:
                raise InvalidBirthday(value)
        elif isinstance(value, Birthday):
            kwargs[key] = value.json()
    elif key == "keep_proxy":
        if not isinstance(value, bool):
            raise ValueError(
                f"Keyword arg `keep_proxy` must be a boolean value; received type(key)={type(key)}."
            )
    elif key in MEMBER_ATTRS [9:]:
        if not value in ("public", "private", None) and not value in Privacy:
            raise ValueError(
                f"Keyword arg `{key}` must be in (None, 'public', 'private') or a Privacy; " \
                f"instead was value={value}."
            )
        if value in Privacy:
            kwargs[key] = value.value # convert Privacy enum to strt

    elif key == "avatar_url":
        if isinstance(value, str):
            async with httpx.AsyncClient() as session:
                response = await session.head(value)
                code = response.status_code
                if code != 200:
                    raise ValueError(
                        f"Invalid URL passed. Received {code} {RESPONSE_CODES[code]}."
                    )
        elif value is not None:
            raise ValueError(f"{key}'s value must be of type str or None")
    elif key == "proxy_tags":
        proxy_tags = []
        for proxy_tag in value:
            if isinstance(proxy_tag, ProxyTag):
                proxy_tags.append(proxy_tag.json()) # convert to dict
            elif isinstance(proxy_tag, dict):
                proxy_tags.append(proxy_tag)
            else:
                raise ValueError(
                    f"Keyword arg `proxy_tags` must be a ProxyTags object, a sequence of " \
                    f"ProxyTag objects, or a sequence of dict containing the keys 'prefix' " \
                    f"and 'suffix'."
                    )
        kwargs[key] = proxy_tags

    return kwargs

async def system_value(key, value):
    if not key in SYSTEM_ATTRS:
        raise InvalidKwarg(key)
    if key in ("name", "description", "tag", "avatar_url") and not isinstance(value, str):
        raise ValueError(f"{key}'s value must be of type string")
    if key == "tz" and not isinstance(value, (Timezone, str)):
        raise ValueError(f"{key}'s value must be of type string or Timezone")
    if key in ("description_privacy", "member_list_privacy", "front_privacy", 
              "front_history_privacy") and not isinstance(value, bool):
        raise ValueError(f"{key}'s value must be of type bool")

