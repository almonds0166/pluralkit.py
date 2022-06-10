
.. currentmodule:: pluralkit

API reference
=============

Client
------

.. autoclass:: Client
   :members:

Models
------

System
~~~~~~

.. autoclass:: System
   :members:

SystemSettings
~~~~~~~~~~~~~~

.. autoclass:: SystemSettings
   :members:

SystemGuildSettings
~~~~~~~~~~~~~~~~~~~

.. autoclass:: SystemGuildSettings
   :members:

Member
~~~~~~

.. autoclass:: Member
   :members:

MemberGuildSettings
~~~~~~~~~~~~~~~~~~~

.. autoclass:: MemberGuildSettings
   :members:

Group
~~~~~

.. autoclass:: Group
   :members:

Switch
~~~~~~

.. autoclass:: Switch
   :members:

Message
~~~~~~~

.. autoclass:: Message
   :members:

Primitives
----------

SystemId
~~~~~~~~

.. autoclass:: SystemId
   :members:

MemberId
~~~~~~~~

.. autoclass:: MemberId
   :members:

GroupId
~~~~~~~

.. autoclass:: GroupId
   :members:

Birthday
~~~~~~~~

.. autoclass:: Birthday
   :members:

Color
~~~~~

.. autoclass:: Color
   :members:

ProxyTag
~~~~~~~~

.. autoclass:: ProxyTag
   :members:

ProxyTags
~~~~~~~~~

.. autoclass:: ProxyTags
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

.. _exceptions:

Exceptions
----------

.. currentmodule:: pluralkit.v2.errors

PluralKitException
~~~~~~~~~~~~~~~~~~

.. autoclass:: PluralKitException

HTTPError
~~~~~~~~~

.. autoclass:: HTTPError

GenericBadRequest
~~~~~~~~~~~~~~~~~

.. autoclass:: GenericBadRequest

NotFound
~~~~~~~~

.. autoclass:: NotFound

SystemNotFound
~~~~~~~~~~~~~~

.. autoclass:: SystemNotFound

MemberNotFound
~~~~~~~~~~~~~~

.. autoclass:: MemberNotFound

GroupNotFound
~~~~~~~~~~~~~

.. autoclass:: GroupNotFound

SwitchNotFound
~~~~~~~~~~~~~~

.. autoclass:: SwitchNotFound

MessageNotFound
~~~~~~~~~~~~~~~

.. autoclass:: MessageNotFound

GuildNotFound
~~~~~~~~~~~~~

.. autoclass:: GuildNotFound

Unauthorized
~~~~~~~~~~~~

.. autoclass:: Unauthorized

NotOwnSystem
~~~~~~~~~~~~

.. autoclass:: NotOwnSystem

NotOwnMember
~~~~~~~~~~~~

.. autoclass:: NotOwnMember

NotOwnGroup
~~~~~~~~~~~

.. autoclass:: NotOwnGroup
