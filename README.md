# pk.py

Asynchronous Python wrapper for [PluralKit](https://pluralkit.me/)'s API. Created with [discord.py](https://github.com/Rapptz/discord.py) in mind.

Currently working on PluralKit's v1.0 API.

## Quick example

```python
from pluralkit.v1 import Client

pk = Client("token")

async for member in pk.get_members():
   print(member.json())
```

## Token

To use the client, you'll need your [PluralKit authorization token](https://pluralkit.me/api/#authentication).

## Links

* [PluralKit v1.0 API](https://app.swaggerhub.com/apis-docs/xSke/PluralKit/1.0#/)
* [PluralKit support server](https://discord.gg/PczBt78)

## Todo

* More obviously: more methods for GETs, edits
* Incorporate character limits to applicable JSON attributes.
* Maybe make an Enum for privacies (namely `{public,private}`)?
* Maybe destruct `ProxyTags` class into just `List[ProxyTag]`?
* Prepare for API v2
* Documentation (namely add attributes docs)

