
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

   - ``build`` is incremented for each latest build, revision, or commit of a minor release.

.. data:: __version__

   A string representation of the version. e.g. ``"1.1.23"``.

.. Most common headings would be New features, Bug fixes, Performance improvements, Miscellaneous

.. _whats_new:

v0.0.1
------

Released Jun 26, 2021.

New features
~~~~~~~~~~~~

Client
^^^^^^

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

Models
^^^^^^

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