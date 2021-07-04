
.. currentmodule:: pluralkit

.. _getting_started:

Getting started
===============

Prerequisites
-------------

pluralkit.py is intended to work with Python 3.6 or higher.

Installing
----------

One can get the package directly from PyPI with the following: ::

   python3 -m pip install -U pluralkit

On Windows, use the `py launcher`_ variation: ::

   py -3 -m pip install -U pluralkit

.. _`py launcher`: https://docs.python.org/3/using/windows.html#getting-started

For `virtual environments`_, use pip like usual: ::

   pip install -U pluralkit

.. _`virtual environments`: https://docs.python.org/3/tutorial/venv.html

To install the unstable version: ::

   git clone https://github.com/almonds0166/pluralkit.py
   cd pluralkit.py
   pip install -U .

Basic concepts
--------------

pluralkit.py uses the `Client` class to coordinate with `PluralKit's API`_ and a handful of classes to work with common PluralKit models such as members, systems, and switches.

Client
~~~~~~

Below is an async example script that prints one's system members and system description, given one's :ref:`authorization token <token>`.

.. code-block:: python

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

.. note::

   By default, the client is meant for asynchronous use; for example, to be paired with `discord.py`_.

Use the ``async_mode=False`` argument for blocking execution:

.. code-block:: python

   from pluralkit import Client

   pk = Client("token", async_mode=False) # your token here

   for member in pk.get_members():
      print(f"{member.name} (`{member.id}`)")

   system = pk.get_system()
   print(system.description)

For demonstration purposes, we'll use the synchronous version of the client on this page.

The User-Agent header may be set with the argument ``user_agent``.

See here for the documentation of the most common Client methods:

- `Client.delete_member`
- `Client.edit_member`
- `Client.edit_system`
- `Client.get_fronters`
- `Client.get_member`
- `Client.get_members`
- `Client.get_message`
- `Client.get_switches`
- `Client.get_system`
- `Client.new_member`
- `Client.new_switch`

.. _`discord.py`: https://discordpy.readthedocs.io/en/stable/
.. _`PluralKit's API`: https://pluralkit.me/

.. _token:

Token
~~~~~

An `authentication token`_ is required to access one's private members or system/member attributes.

To get your system's authentication token, use the ``pk;token`` command. PluralKit will DM you your system's token.

.. important::

   Do not share your system's PluralKit authentication token unless you know what you're doing.

   A new token may be generated (and the old one discarded) by the ``pk;token refresh`` command.

To use the token, pass it as a parameter to the `Client`:

.. code-block:: python

   pk = Client(token)

To store the token more securely, we recommend storing it in a config file such as ``config.py``:

.. code-block:: python

   from config import TOKEN

   pk = Client(TOKEN)

or as an environment variable:

.. code-block:: python

   import os

   TOKEN = os.environ["PLURALKIT_TOKEN"]

   pk = Client(TOKEN)

.. _`authentication token`: https://pluralkit.me/api/#authentication

Models
~~~~~~

The sections below discuss the various models returned by the `Client` methods and how to work with them. In practice, most should only be received via the Client methods, but for others it makes sense to initialize them oneself.

Open a terminal and follow along!

System
^^^^^^

`System` models are returned by the Client methods `Client.get_system` and `Client.edit_system` as well as the `Message.system` attribute. For example::

   >>> from pluralkit import Client
   >>> pk = Client(async_mode=False)
   >>> system = pk.get_system("abcde")
   >>> system
   System('abcde')

Note, as of writing, there is no system with ID ``abcde``, this is just for the sake of example.

System has the following useful attributes:

- `System.avatar_url`
- `System.created`
- `System.description`
- `System.description_privacy`
- `System.front_history_privacy`
- `System.front_privacy`
- `System.id`
- `System.member_list_privacy`
- `System.name`
- `System.tag`
- `System.tz`

Note that the privacy attributes will all be `Privacy.UNKNOWN` unless the Client is using the authorization token corresponding to the system.

Member
^^^^^^

`Member` models are returned by the Client methods `Client.new_member`, `Client.get_member`, `Client.get_members`, and `Client.edit_member` as well as the `Message.member` attribute. For example: ::

   >>> member = pk.get_member("fghij")
   >>> member
   Member('fghij')

Note, as of writing, there is no system with ID ``fghij``, this is just for the sake of example.

Member has the following useful attributes:

- `Member.avatar_privacy`
- `Member.avatar_url`
- `Member.birthday`
- `Member.birthday_privacy`
- `Member.color`
- `Member.created`
- `Member.description`
- `Member.description_privacy`
- `Member.display_name`
- `Member.id`
- `Member.keep_proxy`
- `Member.metadata_privacy`
- `Member.name`
- `Member.name_privacy`
- `Member.pronoun_privacy`
- `Member.pronouns`
- `Member.proxy_tags`
- `Member.visibility`

Switch
^^^^^^

`Switch` models are returned by the Client methods `Client.get_switches` and `Client.new_switch`.

Switch models have the following useful attributes:

- `Switch.timestamp`
- `Switch.members`

Message
^^^^^^^

`Message` models are returned by the Client method `Client.get_message`. For example: ::

   >>> msg = pk.get_message(859884066302984221)
   >>> msg
   Message(859884066302984221)

Message objects have the following useful attributes:

- `Message.channel`
- `Message.id`
- `Message.member`
- `Message.original`
- `Message.sender`
- `Message.system`
- `Message.timestamp`

.. _proxytags:

ProxyTags
^^^^^^^^^

`ProxyTags` objects (not to be confused with :ref:`ProxyTag objects <proxytag>` below) are found under `Member.proxy_tags`. For example: ::

   >>> member.proxy_tags
   ProxyTags<1>

In the example above, this member has a set of one proxy tag.

Like a list or tuple, ProxyTags objects can be iterated through as well as indexed. ::

   >>> pt = member.proxy_tags[0]
   >>> pt
   ProxyTag(prefix='Test:')

And ProxyTags objects have a `~ProxyTags.match` method to determine whether a given string would be proxied by PluralKit.

   >>> member.proxy_tags.match("Hello!")
   False
   >>> member.proxy_tags.match("Test: Hello!")
   True

.. _proxytag:

ProxyTag
^^^^^^^^

`ProxyTag` objects are yielded from `Member.proxy_tags` and represent a single proxy tag. For example: ::

   >>> pt = member.proxy_tags[0]
   >>> pt
   ProxyTag(prefix='Test:')

Each ProxyTag object has an optional `~ProxyTag.prefix` and `~ProxyTag.suffix` attribute: ::

   >>> print(pt.prefix)
   Test:
   >>> pt.suffix is None
   True

Like :ref:`ProxyTags objects above <proxytags>`, ProxyTag objects have a `~ProxyTag.match` method: ::

   >>> pt.match("I hope you're having a good day!")
   False
   >>> pt.match("Test: I hope you're having a good day!")
   True

Color
^^^^^

`Color` objects appear in a member's `~Member.color` attribute.

The Color class has the same behavior as a Color class of the `colour`_ package, which it inherits from. There are a couple ways to initialize the class: ::

   >>> Color("purple") # by web name
   <Color purple>
   >>> Color("#ff00ff") # by hex code
   <Color magenta>

There are a handful of useful methods to work with colors: ::

   >>> c = Color("#ff00ff")
   >>> c.get_hex_l()
   '#ff00ff'
   >>> c.get_web()
   'magenta'
   >>> c.red
   1.0
   >>> c.green
   0.0
   >>> c.blue
   0.9999999999999998

For more information, see the `colour`_ docs.

.. _`colour`: https://pypi.org/project/colour/

Timestamp
^^^^^^^^^

`Timestamp` and `Birthday` objects are similar to `datetime.datetime` objects in that all three have ``year``, ``month``, ``day``, ``hour``, ``minute``, ``second``, and ``microsecond`` attributes, and can be initialized using the respective keyword arguments.

Note that Timestamp and Birthday objects are `mutable`_, whereas datetime objects are immutable, so the ``year``, ``month``, ... attributes may be set directly.

`Timestamp` and `Birthday` objects may also be initialized from a `datetime.datetime` object instead: ::

   >>> from pluralkit import Timestamp
   >>> from datetime import datetime
   >>> dt = datetime.now()
   >>> dt
   datetime.datetime(2021, 6, 26, 11, 17, 39, 103049)
   >>> ts = Timestamp(dt)
   >>> ts
   Timestamp<2021-06-26T11:17:39.103049Z>

Timestamp objects always represent UTC time, and the underlying `datetime.datetime` object, accessed via `Timestamp.datetime`, is timezone aware: ::

   >>> ts.datetime
   datetime.datetime(2021, 6, 26, 18, 17, 39, 103049, tzinfo=<UTC>)

.. _`mutable`: https://medium.com/@meghamohan/mutable-and-immutable-side-of-python-c2145cf72747

Birthday
^^^^^^^^

`Birthday` objects inherit from `Timestamp` objects and can be initialized in the same way. Shown below is the keyword argument method.

   >>> from pluralkit import Birthday
   >>> bd = Birthday(year=2021, month=6, day=26)
   >>> bd
   Birthday<2021-06-26>

Birthdays can be printed as they appear in PluralKit embeds with the ``pk;m [member id]`` command. ::

   >>> print(bd)
   Jun 26, 2021

PluralKit has the ability to hide the year of birthdays. With pluralkit.py, use the `~Birthday.hidden_year` property: ::

   >>> bd.hidden_year = True
   >>> print(bd)
   Jun 26

Timezone
^^^^^^^^

`Timezone` objects are initialized in the same manner that `pytz.timezone` is used, since `pytz` underlies the Timezone class. For example: ::

   >>> from pluralkit import Timezone
   >>> Timezone("UTC")
   Timezone<UTC>
   >>> tz = Timezone("America/Los_Angeles")
   >>> tz
   Timezone<America/Los_Angeles>

The `pytz.tzinfo` object may be accessed by `Timezone.tz`.

Privacy
^^^^^^^

The `Privacy` enumeration is for the privacy attributes of members and systems. For example: ::

   >>> member.description_privacy is Privacy.PUBLIC
   True

There are three types of privacies for pluralkit.py:

- `Privacy.PUBLIC` represents a public PluralKit privacy setting.
- `Privacy.PRIVATE` represents a private PluralKit privacy setting.
- Privacy attributes of members outside of the system associated with the Client instance's :ref:`authentication token <token>` will always appear as `Privacy.UNKNOWN`.

