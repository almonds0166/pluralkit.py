# pk.py

Asynchronous Python wrapper for [PluralKit](https://pluralkit.me/)'s API. Created with [discord.py](https://github.com/Rapptz/discord.py) in mind.

Currently working on PluralKit's v1.0 API.

## Quick example

```python
from pluralkit import Client

pk = Client()

async for member in pk.get_members("abcde"):
   # list members of the system with ID ``abcde``
   print(f"{member.name} (`{member.id})`")
```

## Token

The client can be used without one's [PluralKit authorization token](https://pluralkit.me/api/#authentication), but they'll need it if they'd like to edit their system or access any of their system's private members or info.

## Links

* [PluralKit's API](https://pluralkit.me/)
* [PluralKit support server](https://discord.gg/PczBt78)

## Todo

* Maybe make an Enum for privacies (namely `{public,private}`)?
* Prepare for API v2
* Consider returning datetime.datetime instead of str for system.created property
* Consider returning pytz.timezone instead of str for system.tz property

