# pluralkit.py

Asynchronous Python wrapper for [PluralKit](https://pluralkit.me/)'s API. Created with [discord.py](https://github.com/Rapptz/discord.py) in mind.

Currently working on PluralKit's v1.0 API.

## Quick example

```python
from pluralkit import Client

pk = Client()

async for member in pk.get_members("abcde"):
   # list members of the system with ID ``abcde``
   print(f"{member.name} (`{member.id}`)")
```

## Installing

Python 3.6 or higher is required.

```bash
# linux/MacOS
python3 -m pip install -U pluralkit

# windows
py -3 -m pip install -U pluralkit
```

## Token

The client can be used without one's [PluralKit authorization token](https://pluralkit.me/api/#authentication), but it's required for editing one's system or members or for accessing one's private system or member info.

## Links

* [PyPI link](https://pypi.org/project/pluralkit/)
* [Latest build of the docs](https://pluralkit.readthedocs.io/en/latest/)
* [pluralkit.py Discord support server](https://discord.gg/secvguatbC)
* [PluralKit support server](https://discord.gg/PczBt78)
* [PluralKit's API](https://pluralkit.me/)

## Todo

* Tidy up error handling
* Test timezone mechanics
* Prepare for API v2
