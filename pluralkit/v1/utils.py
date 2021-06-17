from .models import Member, System, ProxyTags, ProxyTag
from .errors import *

from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
)

import datetime
from datetime import datetime as dt
import aiohttp
from colour import Color

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

class Utils(object):
    @staticmethod
    async def member_value(kwargs, key, value):
        if not key in MEMBER_ATTRS:
            raise InvalidKey(key)
        if key == "color":
            try: 
                color = Utils.check_color(value)
            except: 
                color = None
                raise InvalidColor(value)
            finally:
                if color:
                    kwargs[key] = color
        if key == "birthday":
            if isinstance(value, datetime.date):
                kwargs[key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, str):
                try:
                    birthday = dt.strptime(value,'%Y-%m-%d')
                except:
                    birthday = None
                    raise InvalidDate(value)
        if key == "keep_proxy":
            if not isinstance(value, bool):
                raise ValueError("Keep_proxy must be a boolean value")
        if key in MEMBER_ATTRS [9:]:
            if not value is None and not value in ["public", "private"]:
                raise ValueError(f"Must be [None, 'public', 'private'], instead was {value}")
        if key == "avatar_url":
                async with aiohttp.ClientSession() as session:
                        async with session.head(value, ssl=True) as response:
                                if response.status != 200:
                                        raise Exception("Invalid URL passed")
        if key == "proxy_tags":
            for proxy_tag in value:
                if not isinstance(proxy_tag, ProxyTag):
                    raise ValueError("proxy_tags must be a ProxyTags object or a Sequence of Dictionaries containing only the following keys 'prefix' and 'suffix' and with value types of Str")
                    break
            else:
                kwargs[key] = value.json()

        return kwargs

    @staticmethod
    def check_color(color):
        try:
            color2 = Color(color.replace(" ", ""))
        except:
            color2 = None
        finally:
            if color2:
                return color2.hex_l[1:]
            else:
                return None
