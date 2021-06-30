
.. currentmodule:: pluralkit

API reference
=============

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

.. attribute:: Privacy.UNKNOWN

   Equivalent to `Privacy.PUBLIC` in effect. Returned for member and system privacy fields if the client does not have an authorization token set.

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