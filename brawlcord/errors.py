from discord.ext.commands import CommandError


class UserRejected(Exception):
    """Raised when user rejects a challenge"""


class MaintenanceError(CommandError):
    """Raised when the game is on maintenance."""
