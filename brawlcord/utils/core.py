from datetime import datetime

from redbot.core import commands
from redbot.core.commands import Context

from .errors import MaintenanceError


def maintenance():
    """A decorator which checks for maintenance."""

    async def predicate(ctx: Context):
        if await ctx.bot.is_owner(ctx.author):
            # True means command should run
            return True

        cog = ctx.cog
        if cog:
            config = cog.config

            async with config.maintenance() as maint:
                setting = maint["setting"]

                if setting:
                    raise MaintenanceError(
                        "The bot is currently under maintenance. It will end"
                        f" in approx. {maint['duration']} minutes."
                        " Commands will not work till then."
                        " Sorry for the inconvenience!"
                    )
        # Run command if not maintenance
        return True

    return commands.check(predicate)


def utc_timestamp(time: datetime) -> float:
    """Return timestamp in UTC.

    Parameters
    --------------
    time : datetime
        datetime object in UTC

    Returns
    ---------
    float
        Timestamp in UTC
    """

    epoch = datetime(1970, 1, 1)
    # get timestamp in UTC
    timestamp = (time - epoch).total_seconds()

    return timestamp
