
.. currentmodule:: pluralkit

.. _changelog:

Version history
===============

Version related info
--------------------

There are two main ways to query version information about the library.

.. data:: version_info

   A named tuple of the form ``major.minor.build``, where:

   - ``major`` is a major release, representing either many new features or a significant refactor to the underlying API or API wrapper.

   - ``minor`` is a minor release, representing some new features on the given major release.

   - ``build`` is incremented for each latest build, patch, or revision of a minor release.

.. data:: __version__

   A string representation of the version. e.g. ``"1.1.23"``.

.. Most common headings would be New features, Fixes, Improvements

.. _whats_new:

v1.1.0 (December 30, 2022)
--------------------------

- Bug fixes
- New attributes for own system:
   - `Member.message_count`
   - `Member.last_message_timestamp`
- Interface with autoproxy settings:
   - `Member` models now have an `~Member.autoproxy_enabled` attribute
   - New `Client.get_autoproxy_settings` method
   - New `Client.update_autoproxy_settings` method

v1.0.0 (June 10, 2022)
----------------------

- Total upgrade to PluralKit API v2! (finally!)
- Revamped model organization and 33 client methods
- Smarter rate limiting
- Low-level bug fixes

v0.1.2 (July 13, 2021)
----------------------

New features
~~~~~~~~~~~~

- Added rate limiting (at most 1 request per half second).
- Added rich comparison to the `Timestamp` class, so Timestamp objects can be compared with other Timestamp objects or with `datetime.datetime` objects.
- `Client.get_fronters` can now accept Discord IDs.
- `Client.get_switches` can now accept Discord IDs.

Improvements
~~~~~~~~~~~~

- Improved clarity & accuracy of pluralkit.py :ref:`exceptions <exceptions>`.

v0.1.0 (July 12, 2021)
----------------------

New features
~~~~~~~~~~~~

- Added synchronous support with ``async_mode=False`` in `Client`.
- Switched over from `aiohttp`_ to `httpx`_.
- `Client.edit_system` and `Client.edit_member` can now take an optional `System` and `Member` argument, respectively.
- Added equality methods to the model classes.

Fixes
~~~~~

- Fixed `Birthday` from raising `ValueError` for member birthdays with hidden years.
- Raise `~errors.MemberNotFound` exception for invalid member IDs in `Client.get_member`.
- Fixed `Member.color` attribute.

.. _`aiohttp`: https://docs.aiohttp.org/en/stable/
.. _`httpx`: https://www.python-httpx.org/

v0.0.1 (Jun 26, 2021)
---------------------

New features
~~~~~~~~~~~~

- `Client` class to coordinate with the PluralKit v1 API.
- `Client.delete_member` method to delete a member of one's system.
- `Client.edit_member` method to edit a member of one's system.
- `Client.edit_system` method to edit one's system.
- `Client.get_fronters` method to retrieve a system's current fronters.
- `Client.get_member` method to retrieve a member by their ID.
- `Client.get_members` method to retrieve a list of a system's members.
- `Client.get_message` method to retrieve information about a proxied message.
- `Client.get_switches` method to retrieve a system's switch history.
- `Client.get_system` method to retrieve a system.
- `Client.new_member` method to create a new member of one's system.
- `Client.new_switch` method to log a new switch in one's system.
- `System` class to represent PluralKit systems.
- `Member` class to represent PluralKit system members.
- `Switch` class to represent switches.
- `Message` class to represent proxied messages.
- `ProxyTag` class to represent member proxy tags.
- `ProxyTags` class to represent sets of proxy tags.
- `Color` class to represent member colors.
- `Timestamp` class to represent PluralKit timestamps.
- `Birthday` class to represent member birthdays.
- `Timezone` class to represent PluralKit timezones.
- `Privacy` enumeration to represent PluralKit privacy settings.
