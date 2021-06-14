from .models import Member, System, ProxyTags, Colour
from .errors import *

from typing import (
   Any,
   Union, Optional,
   Tuple, List, Set, Sequence, Dict,
   AsyncIterable, 
)

import datetime
import aiohttp

member_attrs = [
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
      "metadata_privacy"
      ]

class Utils(object):

  @staticmethod
  def pack_member(item):
    return Member(
      id=item["id"],
      name=item["name"],
      name_privacy=item["name_privacy"],
      created=item["created"],
      display_name=item["display_name"],
      description=item["description"],
      description_privacy=item["description_privacy"],
      color=item["color"],
      birthday=item["birthday"],
      birthday_privacy=item["birthday_privacy"],
      pronouns=item["pronouns"],
      pronoun_privacy=item["pronoun_privacy"],
      avatar_url=item["avatar_url"],
      avatar_privacy=item["avatar_privacy"],
      keep_proxy=item["keep_proxy"],
      metadata_privacy=item["metadata_privacy"],
      proxy_tags=ProxyTags.from_dict(item["proxy_tags"]),
      visibility=item["visibility"],
    )

  @staticmethod
  def pack_system(resp):
    return System(
      id=resp["id"],
      name=resp["name"],
      description=resp["description"],
      tag=resp["tag"],
      avatar_url=resp["avatar_url"],
      tz=resp["tz"],
      created=resp["created"],
      description_privacy=resp["description_privacy"],
      member_list_privacy=resp["member_list_privacy"],
      front_privacy=resp["front_privacy"],
      front_history_privacy=resp["front_history_privacy"]
    )

  @staticmethod
  async def member_value(kwargs, key, value):
    if not key in member_attrs:
      raise InvalidKey(key)
    elif key == "color":
      try: 
        color = Colour(color=value)
      except: 
        raise InvalidColor(value)
      finally:
        kwargs[key] = color.id
    elif key == "birthday":
      if isinstance(value, datetime.date):
        kwargs[key] = value.strftime("%Y-%m-%d")
      elif isinstance(value, str):
        try:
          birthday = datetime.strptime(value,'%Y-%m-%d')
        except:
          raise InvalidDate(value)
        finally:
          kwargs[key] = birthday
    elif key == "keep_proxy":
      if not isinstance(value, bool):
        raise ValueError("Keep_proxy must be a boolean value")
    elif key in member_attrs [9:]:
      if not value is None and not value in ["public", "private"]:
        raise ValueError(f"Must be [None, 'public', 'private'], instead was {value}")
    elif key == "avatar_url":
        async with aiohttp.ClientSession() as session:
            async with session.head(value, ssl=True) as response:
                if response.status != 200:
                    raise Exception("Invalid URL passed")
    elif key == "proxy_tags":
      if not isinstance(value, Sequence):
        raise ValueError("proxy_tags Must be a Sequence")
      else:
        if not all(isinstance(item, Dict) for item in value):
          raise ValueError("proxy_tags Must be a Sequence of Dicts containing proxy tags")
        else:
          for proxy_tags in value:
            for key, value in proxy_tags.items():
              if not key in ["prefix", "suffix"]:
                raise ValueError("Only ['prefix', 'suffix'] can be fields in a proxy tag")
              if not isinstance(value, str):
                raise ValueError("Values must be Str")

    return kwargs
