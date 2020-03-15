from datetime import datetime

from redbot.core import Config
from redbot.core.commands.context import Context
from redbot.core.utils.chat_formatting import humanize_timedelta


async def user_cooldown(rate: int, per: int, config: Config, ctx: Context):
    """Handle user cooldown"""

    async with config.user(ctx.author).cooldown() as cooldown:
        if ctx.command.qualified_name not in cooldown:
            cooldown[ctx.command.qualified_name] = {
                "last": utc_timestamp(datetime.utcnow()),
                "rate": rate,
                "per": per,
                "uses": 1
            }
            return True
        else:
            if await check_user_cooldown(ctx, config, cooldown):
                return True
    return False


async def check_user_cooldown(ctx: Context, config: Config, cooldown: dict):
    """Check if command is on cooldown."""

    command = ctx.command.qualified_name

    last = cooldown[command]["last"]
    rate = cooldown[command]["rate"]
    per = cooldown[command]["per"]
    uses = cooldown[command]["uses"]

    now = utc_timestamp(datetime.utcnow())

    if now >= last + per:
        cooldown[command] = {
            "last": utc_timestamp(datetime.utcnow()),
            "rate": rate,
            "per": per,
            "uses": 1
        }
        return True
    else:
        if uses < rate:
            cooldown[command] = {
                "last": last,
                "rate": rate,
                "per": per,
                "uses": uses + 1
            }
            return True
    return False


async def user_cooldown_msg(ctx: Context, config: Config):
    """Return cooldown message with time remaining."""

    async with config.user(ctx.author).cooldown() as cooldown:
        command = ctx.command.qualified_name

        per = cooldown[command]["per"]
        last = cooldown[command]["last"] + per
        now = utc_timestamp(datetime.utcnow())

        return (
                "This command is on cooldown. Try again in {}.".format(
                    humanize_timedelta(seconds=last-now) or "1 second"
                )
            )


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
