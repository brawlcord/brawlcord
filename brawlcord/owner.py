import logging

import discord
from redbot.core import checks, commands
from redbot.core.commands import Context

from .abc import MixinMeta

log = logging.getLogger("red.brawlcord.owner")


class OwnerMixin(MixinMeta):
    """Class for owner-only commands."""

    @commands.command(name="botinfo")
    @checks.is_owner()
    async def _bot_info(self, ctx: Context):
        """Display bot statistics"""

        total_guilds = len(self.bot.guilds)
        total_users = len(await self.config.all_users())

        await ctx.send(f"Total Guilds: {total_guilds}\nTotal Users: {total_users}")

    @commands.command()
    @checks.is_owner()
    async def clear_cooldown(self, ctx: Context, user: discord.User = None):
        if not user:
            user = ctx.author
        async with self.config.user(user).cooldown() as cooldown:
            cooldown.clear()

    @commands.command()
    @checks.is_owner()
    async def add_mega(self, ctx: Context, quantity=1):
        """Add a mega box to each user who has used the bot at least once."""

        users_data = await self.config.all_users()
        user_ids = users_data.keys()

        for user_id in user_ids:
            try:
                user_group = self.config.user_from_id(user_id)
            except Exception:
                log.exception(f"Couldn't fetch user group of {user_id}.")
                continue
            try:
                async with user_group.gifts() as gifts:
                    gifts["megabox"] += quantity
            except Exception:
                log.exception(f"Couldn't fetch gifts for {user_id}.")
                continue

        await ctx.send(
            f"Added {quantity} mega boxes to all users (bar errors)."
        )

    @commands.command(aliases=["maintenance"])
    @checks.is_owner()
    async def maint(
        self, ctx: Context, setting: bool = False, duration: int = None
    ):
        """Set/remove maintenance. The duration should be in minutes."""

        if duration:
            setting = True

        async with self.config.maintenance() as maint:
            maint["setting"] = setting
            maint["duration"] = duration if duration else 0

        if setting:
            await ctx.send(
                f"Maintenance set for {duration} minutes."
                " Commands will be disabled until then."
            )
        else:
            await ctx.send("Disabled maintenance. Commands are enabled now.")

    @commands.command(aliases=["maintinfo"])
    @checks.is_owner()
    async def minfo(self, ctx: Context):
        """Display maintenance info."""

        async with self.config.maintenance() as maint:
            setting = maint["setting"]
            duration = maint["duration"]

        await ctx.send(f"**Setting:** {setting}\n**Duration:** {duration}")

    @commands.command()
    @checks.is_owner()
    async def fixskins(self, ctx: Context):
        """Removes empty lists from the skins list."""

        data = await self.config.all_users()

        await ctx.trigger_typing()
        for user in data:
            for brawler in data[user]["brawlers"]:
                skins = data[user]["brawlers"][brawler]["skins"]

                skins = [skin for skin in skins if skin]
                user_obj = discord.Object(user)
                try:
                    await self.config.user(user_obj).set_raw(
                        "brawlers", brawler, "skins", value=skins
                    )
                except Exception:
                    log.error(f"Error fixing skins for user with ID: {user}")

        await ctx.send("Done! Please check logs for errors.")
