
from http.client import responses as RESPONSE_CODES

__all__ = (
    "PluralKitException",
    "AuthorizationError",
    "SystemNotFound",
    "MemberNotFound",
    "DiscordUserNotFound",
    "AccessForbidden",
    "InvalidKwarg",
    "InvalidColor",
    "InvalidBirthday",
    "HTTPError"
)

class PluralKitException(Exception):
    """Base exception class for pk.py
    """
    ...

class AuthorizationError(PluralKitException):
    """Thrown when the authorization token passed to PluralKit's API is invalid (or missing).
    """
    def __init__(self):
        super().__init__((
            "System token seems to be missing or invalid. Can you check that you entered it in "
            "correctly?"
        ))

class SystemNotFound(PluralKitException):
    """Thrown when the system ID is apparently not in PluralKit's database.
    """
    def __init__(self, id):
        super().__init__(
            f"System with the given ID ({id}) was not found."
        )

class MemberNotFound(PluralKitException):
    """Thrown when the member ID is apparently not in PluralKit's database.
    """
    def __init__(self, id):
        super().__init__(
            f"Member with the given ID ({id}) was not found."
        )

class DiscordUserNotFound(PluralKitException):
    """Thrown when the Discord user ID is apparently not associated with a PluralKit system.
    """
    def __init__(self, id):
        super().__init__(
            f"The given Discord user ID ({id}) does not seem to correspond to any systems."
        )

class AccessForbidden(PluralKitException):
    """Thrown when attempting to access private info.
    """
    def __init__(self):
        super().__init__((
            "The system's requested info is private and the client authorization token is either "
            "missing, invalid, or does not correspond to the requested system."
        ))

class InvalidKwarg(PluralKitException):
    """
    Thrown when an invalid field is passed in a POST or PATCH request
    """
    def __init__(self, key):
        super().__init__(
            f"A keyworded argument was passed that will not be accepted by the server: `{key}`"
        )

class InvalidColor(PluralKitException):
    """
    Thrown when an invalid color is passed in a POST or PATCH request
    """
    def __init__(self, color):
        super().__init__(
                f"Given value is not a string or Color object: `{color}`"
            )

class InvalidBirthday(PluralKitException):
    """
    Thrown when an invalid string is passed for the "Birthday" field of a member object. 
    (Must be yyyy-mm-dd)
    """
    def __init__(self, string):
        super().__init__(
            f"`{string}` is not a valid yyyy-mm-dd date or datetime.datetime object"
        )

class HTTPError(PluralKitException):
    """Thrown when 
    """
    def __init__(self, status_code):
        super().__init__(
            f"Received unexpected HTTP code '{status_code} {RESPONSE_CODES[status_code]}'. " \
            f"Check your connection or whether PluralKit's API is up."
        )