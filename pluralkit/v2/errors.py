
from http.client import responses as RESPONSE_CODES

class PluralKitException(Exception):
    """Base exception class for pluralkit.py
    """
    ...

class HTTPError(PluralKitException):
    """HTTP exception class for PluralKit errors
    """

class GenericBadRequest(PluralKitException):
    """
    """

class ModelParseError(PluralKitException):
    """
    """

class ValidationError(PluralKitException):
    """
    """

class NotFound(PluralKitException):
    """Exception class for "not found"-related errors
    """
    def __init__(self, id_=None):
        Exception.__init__(self, (
            f"The given {self.CONTEXT} ID ({id_}) was not found in PluralKit's database."
        ))

class SystemGuildNotFound(NotFound):
    """
    """

class MemberGuildNotFound(NotFound):
    """
    """

class MemberNotFound(NotFound):
    """Thrown when the Member ID is apparently not in PluralKit's database.
    """
    CONTEXT = "Member"

class SystemNotFound(NotFound):
    """Thrown when the System ID is apparently not in PluralKit's database.
    """
    CONTEXT = "System"

class SwitchNotFound(NotFound):
    """Thrown when the Switch ID is apparently not in PluralKit's database.
    """
    CONTEXT = "Switch"

class SwitchNotFoundPublic(NotFound):
    """
    """

class MessageNotFound(NotFound):
    """Thrown when the message ID is apparently not in PluralKit's database.
    """
    CONTEXT = "Message"

class GroupNotFound(NotFound):
    """Thrown when the Group ID is apparently not in PluralKit's database.
    """
    CONTEXT = "Group"

class NotOwnError(PluralKitException):
    """Thrown when attempting to access private info.
    """
    def __init__(self, id_=None):
        Exception.__init__(self, (
            f"You do not seem to own the {self.CONTEXT} associated with the ID {id_}. Please make "
            f"sure you have your correct authorization token loaded!"
        ))

class NotOwnMemberError(NotOwnError):
    """
    """
    CONTEXT = "Member"

class NotOwnGroupError(NotOwnError):
    """
    """
    CONTEXT = "Group"

# Exceptions related to lack of authorization

class Unauthorized(PluralKitException):
    """Thrown when the authorization token passed to PluralKit's API is invalid or missing.
    """
    def __init__(self):
        Exception.__init__(self, (
            f"System token seems to be missing or invalid. Can you check that you entered it in "
            f"correctly?"
        ))

class UnauthorizedGroupList(Unauthorized):
    """
    """

class UnauthorizedGroupMemberList(Unauthorized):
    """
    """

class UnauthorizedMemberList(Unauthorized):
    """
    """

class UnauthorizedFrontHistory(Unauthorized):
    """
    """

class UnauthorizedCurrentFronters(Unauthorized):
    """
    """

# Exceptions related to switch logging

class SwitchError(PluralKitException):
    """
    """

class DuplicateMembersInList(SwitchError):
    """
    """

class SameSwitchTimestampError(SwitchError):
    """
    """

class SameSwitchMembersError(SwitchError):
    """
    """

class InvalidSwitchId(SwitchError):
    """
    """
