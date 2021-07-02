# pluralkit.py

Python wrapper for [PluralKit](https://pluralkit.me/)'s API.

Currently supports PluralKit's v1.0 API.

## Installing

Python 3.6 or higher is required.

```bash
# linux/macOS
python3 -m pip install -U pluralkit

# windows
py -3 -m pip install -U pluralkit
```

## Quick examples

Provided a system's authorization token, the examples below print the system description and list the system's members.

### Async usage

pluralkit.py was created with [discord.py](https://github.com/Rapptz/discord.py) in mind, and so the default implementation is [asynchronous](https://docs.python.org/3/library/asyncio-task.html).

```python
from pluralkit import Client
import asyncio

pk = Client("token") # your token here

async def main():
   system = await pk.get_system()
   print(system.description)

   members = pk.get_members()
   async for member in members:
      print(f"{member.name} (`{member.id}`)")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### Synchronous usage

Blocking execution may be specified with the client argument `async_mode=False`.

```python
from pluralkit import Client

pk = Client("token", async_mode=False)

system = pk.get_system()
print(system.description)

members = pk.get_members()
for member in members:
   print(f"{member.name} (`{member.id}`)")
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
