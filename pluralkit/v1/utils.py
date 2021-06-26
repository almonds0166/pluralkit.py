
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)
import datetime
from http.client import responses as RESPONSE_CODES

import aiohttp
import colour
import pytz

from .models import ProxyTag, Privacy, Timezone
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

async def member_value(kwargs, key, value):
    """Prepares the kwargs given to `~v1.client.Client` methods for PluralKit's API, for internal
    use.
    """
    if not key in MEMBER_ATTRS:
        raise InvalidKwarg(key)
    if key == "color":
        if value is not None:
            kwargs[key] = parse_color(value).hex_l[1:]
    elif key == "birthday":
        if isinstance(value, datetime.date): # will catch Timestamp and Birthday objects
            kwargs[key] = value.strftime("%Y-%m-%d")
        elif isinstance(value, str):
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except:
                raise InvalidBirthday(value)
    elif key == "keep_proxy":
        if not isinstance(value, bool):
            raise ValueError(
                f"Keyword arg `keep_proxy` must be a boolean value; received {type(key)=}."
            )
    elif key in MEMBER_ATTRS [9:]:
        if not value in ("public", "private", None) and not value in Privacy:
            raise ValueError(
                f"Keyword arg `{key}` must be in (None, 'public', 'private') or a Privacy; " \
                f"instead was {value=}."
            )
        if value in Privacy:
            kwargs[key] = value.value # convert Privacy enum to str
    elif key == "avatar_url":
        async with aiohttp.ClientSession() as session:
            async with session.head(value, ssl=True) as response:
                code = response.status
                if code != 200:
                    raise ValueError(
                        f"Invalid URL passed. Received {code} {RESPONSE_CODES[code]}."
                    )
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

async def system_value(kwargs, key, value):
    if not key in SYSTEM_ATTRS:
        raise InvalidKwarg(key)
    if key in ("name", "description", "tag", "avatar_url") and not isinstance(value, str):
        raise ValueError(f"{key}'s value must be of type string")
    if key == "tz" and not isinstance(value, (Timezone, str)):
        raise ValueError(f"{key}'s value must be of type string or Timezone")
    if key in ("description_privacy", "member_list_privacy", "front_privacy", "front_history_privacy") and not isinstance(value, bool):
        raise ValueError(f"{key}'s value must be of type bool")
