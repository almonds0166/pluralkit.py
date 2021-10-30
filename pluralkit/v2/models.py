
from string import ascii_lowercase as ALPHABET
from enum import Enum

# Enums

class Privacy(Enum):
     """Represents the privacies accepted by PluralKit.
     """
     PUBLIC = "public"
     PRIVATE = "private"
     #UNKNOWN = None # legacy, effectively resets privacy to "public"

class AutoproxyMode(Enum):
    """Represents a system's autoproxy mode for `SystemGuildSettings`.
    """
    OFF = 1
    FRONT = 2
    LATCH = 3
    MEMBER = 4

# Base class for all models

class Model:
    """Base class for all models.
    """

    @classmethod
    def from_json(cls, obj: dict):
        """Convert the given JSON object to an instance of this model class.

        Throws a TypeError if the given object is invalid for the given class.

        Args:
            obj: The JSON object to parse.
        """
        return Model()

    def json(self):
        """Return the JSON object representing this model.
        """
        return None

# IDs

class PluralKitId(Model):
    """Base class for PluralKit IDs
    """
    def __init__(self, id_: str):
        assert len(id_) == 5 and all(c in ALPHABET for c in id_), \
            f"{self.CONTEXT} ID should be a five-character lowercase string."

        self.id_ = id_

    def __str__(self):
        return f"{self.id_}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id_})"

    json = __str__

class MemberId(PluralKitId):
    """Member IDs
    """
    CONTEXT = "Member"

class SystemId(PluralKitId):
    """System IDs
    """
    CONTEXT = "System"

class SwitchId(PluralKitId):
    """Switch IDs
    """
    CONTEXT = "Switch"

class GroupId(PluralKitId):
    """Group IDs
    """
    CONTEXT = "Group"

# Primitives

class Color(Model):
    """
    """

class Timestamp(Model):
    """
    """

class Birthday(Model):
    """
    """

class Timezone(Model):
    """
    """

# Settings

class MemberGuildSettings(Model):
    """
    """

class SystemGuildSettings(Model):
    """
    """

# Proxy tags

class ProxyTag(Model):
    """
    """

class ProxyTags(Model):
    """
    """

# Member, System, Group, Switch

class Member(Model):
    """
    """

class System(Model):
    """
    """

class Group(Model):
    """
    """

class Switch(Model):
    """
    """
