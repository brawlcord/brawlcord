from discord.ext.commands import CheckFailure


class UserRejected(Exception):
    """Raised when user rejects a challenge"""


class MaintenanceError(CheckFailure):
    """Raised when the game is on maintenance."""
