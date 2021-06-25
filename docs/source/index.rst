.. pk.py documentation master file, created by
   sphinx-quickstart on Sat Jun 12 15:44:22 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. currentmodule:: pluralkit

Welcome to pk.py's documentation!
=================================

pk.py is an asynchronous Python wrapper for `PluralKit's API`_ created with `discord.py`_ in mind.

.. _`PluralKit's API`: https://pluralkit.me/
.. _`discord.py`: https://discordpy.readthedocs.io/en/stable/

Contents
--------

.. toctree::
   :maxdepth: 4

   api

Quick start
-----------

This module operates around the `pluralkit.Client` class.

Here's an example script that simply prints one's system members, given their `authorization token`_.

.. code-block:: python

   import asyncio
   from pluralkit import Client

   async def main():
      pk = Client("token") # your token here

      async for member in pk.get_members():
         print(f"{member.name} (`{member.id}`)")

   if __name__ == "__main__":
      asyncio.get_event_loop().run_until_complete(main())

.. _`authorization token`: https://pluralkit.me/api/#authentication

Links
-----

- `PluralKit's API`_
- `PluralKit support server`_

.. _`PluralKit's API`: https://pluralkit.me/
.. _`PluralKit support server`: https://discord.gg/PczBt78

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
