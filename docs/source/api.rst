
.. currentmodule:: pluralkit

API reference
=============

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

Client
------

.. autoclass:: Client
   :members:

Models
------

Birthday
~~~~~~~~

.. autoclass:: Birthday
   :members:

Color
~~~~~

.. autoclass:: Color
   :members:

Member
~~~~~~

.. autoclass:: Member
   :members:

Message
~~~~~~~

.. autoclass:: Message
   :members:

ProxyTag
~~~~~~~~

.. autoclass:: ProxyTag
   :members:

ProxyTags
~~~~~~~~~

.. autoclass:: ProxyTags
   :members:

Switch
~~~~~~

.. autoclass:: Switch
   :members:

System
~~~~~~

.. autoclass:: System
   :members:

Timestamp
~~~~~~~~~

.. autoclass:: Timestamp
   :members:

Timezone
~~~~~~~~

.. autoclass:: Timezone
   :members:

Enumerations
------------

Privacy
~~~~~~~

.. attribute:: Privacy.PUBLIC

   Represents a public PluralKit privacy setting.

.. attribute:: Privacy.PRIVATE

   Represents a private PluralKit privacy setting.

.. attribute:: Privacy.NULL

   Equivalent to `Privacy.PUBLIC` in effect. Intended for internal use.

Exceptions
----------

PluralKitException
~~~~~~~~~~~~~~~~~~

.. autoclass:: errors.PluralKitException
   :members:

AccessForbidden
~~~~~~~~~~~~~~~

.. autoclass:: errors.AccessForbidden
   :members:

AuthorizationError
~~~~~~~~~~~~~~~~~~

.. autoclass:: errors.AuthorizationError
   :members:

DiscordUserNotFound
~~~~~~~~~~~~~~~~~~~

.. autoclass:: errors.DiscordUserNotFound
   :members:

InvalidBirthday
~~~~~~~~~~~~~~~

.. autoclass:: errors.InvalidBirthday
   :members:

InvalidColor
~~~~~~~~~~~~

.. autoclass:: errors.InvalidColor
   :members:

InvalidKwarg
~~~~~~~~~~~~

.. autoclass:: errors.InvalidKwarg
   :members:

SystemNotFound
~~~~~~~~~~~~~~

.. autoclass:: errors.SystemNotFound
   :members: