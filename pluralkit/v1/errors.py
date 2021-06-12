
__all__ = (
   "PluralKitException",
   "AuthorizationError",
   "SystemNotFound",
   "DiscordUserNotFound",
   "AccessForbidden"
)

class PluralKitException(Exception):
   """Base exception class for pk.py
   """
   ...

class AuthorizationError(PluralKitException):
   """Thrown when the authorization token passed to PluralKit's API is invalid (or missing).
   """
   def __init__(self):
      super().__init__(
         "System token seems to be invalid. Can you check that you entered it in correctly?"
      )

class SystemNotFound(PluralKitException):
   """Thrown when the system ID is apparently not in PluralKit's database.
   """
   def __init__(self, id):
      super().__init__(
         f"System with the given ID (`{id}`) was not found."
      )

class DiscordUserNotFound(PluralKitException):
   """Thrown when the Discord user ID is apparently not associated with a PluralKit system.
   """
   def __init__(self, id):
      super().__init__(
         f"The given user ID (`{id}`) does not seem to correspond to any systems."
      )

class AccessForbidden(PluralKitException):
   """Thrown when a system's list of members is private.
   """
   def __init__(self):
      super().__init__((
         "The system's member list is private and the client authorization token is either "
         "missing, invalid, or does not correspond to the system."
      ))