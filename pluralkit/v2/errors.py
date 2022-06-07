
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

# Exceptions related to lack of authorization

class Unauthorized(PluralKitException):
    """Thrown when the authorization token passed to PluralKit's API is invalid or missing.
    """

class NotOwnSystem(Unauthorized):
    """
    """

class NotOwnMember(Unauthorized):
    """
    """
    CONTEXT = "Member"

class NotOwnGroup(Unauthorized):
    """
    """
    CONTEXT = "Group"

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

GENERIC_ERROR_CODE_LOOKUP = {
    400: GenericBadRequest,
    403: Unauthorized,
    404: NotFound,
}

SYSTEM_ERROR_CODE_LOOKUP = GENERIC_ERROR_CODE_LOOKUP | {
    401: Unauthorized,
    403: NotOwnSystem,
    404: SystemNotFound,
}

MEMBER_ERROR_CODE_LOOKUP = GENERIC_ERROR_CODE_LOOKUP | {
    401: Unauthorized,
    403: NotOwnMember,
    404: MemberNotFound,
}

GROUP_ERROR_CODE_LOOKUP = GENERIC_ERROR_CODE_LOOKUP | {
    401: Unauthorized,
    403: NotOwnGroup,
    404: GroupNotFound,
}

MESSAGE_ERROR_CODE_LOOKUP = GENERIC_ERROR_CODE_LOOKUP | {
    401: Unauthorized,
    404: MessageNotFound,
}

SWITCH_ERROR_CODE_LOOKUP = GENERIC_ERROR_CODE_LOOKUP | {
    401: Unauthorized,
    403: NotOwnSystem,
    404: SwitchNotFound,
}
