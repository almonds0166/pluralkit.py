
from http.client import responses as RESPONSE_CODES

class PluralKitException(Exception):
    """Base exception class for pluralkit.py
    """

class HTTPError(PluralKitException):
    """General PluralKit exception class for unexpected HTTP codes (e.g. 500).
    """

class GenericBadRequest(PluralKitException):
    """Thrown when the API server informs the client that the request was malformed (400).
    """

# Exceptions related to "not found"-related errors

class NotFound(PluralKitException):
    """Thrown when the resource cannot be found (404).
    """

class MemberNotFound(NotFound):
    """Thrown when the Member ID is apparently not in PluralKit's database (404).
    """

class SystemNotFound(NotFound):
    """Thrown when the System ID is apparently not in PluralKit's database (404).
    """

class SwitchNotFound(NotFound):
    """Thrown when the Switch ID is apparently not in PluralKit's database (404).
    """

class MessageNotFound(NotFound):
    """Thrown when the message ID is apparently not in PluralKit's database (404).
    """

class GroupNotFound(NotFound):
    """Thrown when the Group ID is apparently not in PluralKit's database (404).
    """

class GuildNotFound(NotFound):
    """Thrown when the member or system has no guild settings for a given guild (404).
    """

# Exceptions related to lack of authorization

class Unauthorized(PluralKitException):
    """Thrown when the authorization token passed to PluralKit's API is invalid or missing (403).
    """

class NotOwnSystem(Unauthorized):
    """Thrown when the client doesn't have access to a system's private info (403).
    """

class NotOwnMember(Unauthorized):
    """Thrown when the client doesn't have access to a member's private info (403).
    """

class NotOwnGroup(Unauthorized):
    """Thrown when the client doesn't have access to a group's private info (403).
    """

# Python <= 3.8 RTD fix
def merge(d1, d2): return {**d1, **d2}

GENERIC_ERROR_CODE_LOOKUP = {
    400: GenericBadRequest,
    403: Unauthorized,
    404: NotFound,
}

SYSTEM_ERROR_CODE_LOOKUP = merge(GENERIC_ERROR_CODE_LOOKUP, {
    401: Unauthorized,
    403: NotOwnSystem,
    404: SystemNotFound,
})

MEMBER_ERROR_CODE_LOOKUP = merge(GENERIC_ERROR_CODE_LOOKUP, {
    401: Unauthorized,
    403: NotOwnMember,
    404: MemberNotFound,
})

GROUP_ERROR_CODE_LOOKUP = merge(GENERIC_ERROR_CODE_LOOKUP, {
    401: Unauthorized,
    403: NotOwnGroup,
    404: GroupNotFound,
})

MESSAGE_ERROR_CODE_LOOKUP = merge(GENERIC_ERROR_CODE_LOOKUP, {
    401: Unauthorized,
    404: MessageNotFound,
})

SWITCH_ERROR_CODE_LOOKUP = merge(GENERIC_ERROR_CODE_LOOKUP, {
    401: Unauthorized,
    403: NotOwnSystem,
    404: SwitchNotFound,
})

GUILD_ERROR_CODE_LOOKUP = merge(GENERIC_ERROR_CODE_LOOKUP, {
    401: Unauthorized,
    404: GuildNotFound,
})
