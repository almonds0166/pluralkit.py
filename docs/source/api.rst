
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

.. autoclass:: Privacy

   .. autoattribute:: Privacy.PUBLIC

      Represents a public PluralKit privacy setting.

   .. autoattribute:: Privacy.PRIVATE

      Represents a private PluralKit privacy setting.

   .. autoattribute:: Privacy.UNKNOWN

      Equivalent to `Privacy.PUBLIC` in effect. Returned for member and system privacy fields if the client does not have an authorization token set.

Exceptions
----------

PluralKitException
~~~~~~~~~~~~~~~~~~

.. autoclass:: errors.PluralKitException

AccessForbidden
~~~~~~~~~~~~~~~

.. autoclass:: errors.AccessForbidden

AuthorizationError
~~~~~~~~~~~~~~~~~~

.. autoclass:: errors.AuthorizationError

DiscordUserNotFound
~~~~~~~~~~~~~~~~~~~

.. autoclass:: errors.DiscordUserNotFound

InvalidBirthday
~~~~~~~~~~~~~~~

.. autoclass:: errors.InvalidBirthday

InvalidColor
~~~~~~~~~~~~

.. autoclass:: errors.InvalidColor

InvalidKwarg
~~~~~~~~~~~~

.. autoclass:: errors.InvalidKwarg

SystemNotFound
~~~~~~~~~~~~~~

.. autoclass:: errors.SystemNotFound

MemberNotFound
~~~~~~~~~~~~~~

.. autoclass:: errors.MemberNotFound
