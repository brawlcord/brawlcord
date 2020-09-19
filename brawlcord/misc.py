import asyncio
import json
import logging
import re
import urllib.request
from datetime import datetime
from distutils.version import LooseVersion

import discord
from redbot.core import commands, checks
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import humanize_timedelta, text_to_file
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate

from .abc import MixinMeta
from .utils.constants import (
    BRAWLSTARS,
    BRAWLCORD_CODE_URL,
    COMMUNITY_SERVER,
    EMBED_COLOR,
    FAN_CONTENT_POLICY,
    INVITE_URL,
    REDDIT_LINK,
    SOURCE_LINK
)
from .utils.core import maintenance

# NOTE: `.brawlcord.__version__` is imported in `MiscMixin._brawlcord` method
# to avoid circular imports.

log = logging.getLogger("red.brawlcord.misc")


class MiscMixin(MixinMeta):
    """Class for all miscellaneous commands."""

    @commands.command(name="report")
    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
    @maintenance()
    async def _report(self, ctx: Context, *, msg: str):
        """Send a report to the bot owner"""

        report_str = (
            f"`{datetime.utcnow().replace(microsecond=0)}` {ctx.author}"
            f" (`{ctx.author.id}`) reported from `{ctx.guild or 'DM'}`: **{msg}**"
        )

        channel_id = await self.config.report_channel()

        channel = None
        if channel_id:
            channel = self.bot.get_channel(channel_id)

        if channel:
            await channel.send(report_str)
        else:
            owner = self.bot.get_user(self.bot.owner_id)
            await owner.send(report_str)

        await ctx.send(
            "Thank you for sending a report. Your issue"
            " will be resolved as soon as possible."
        )

    @_report.error
    async def report_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                "This command is on cooldown. Try again in {}.".format(
                    humanize_timedelta(seconds=error.retry_after) or "1 second"
                ),
                delete_after=error.retry_after,
            )
        else:
            log.exception(type(error).__name__, exc_info=error)

    @commands.command(name="rchannel")
    @checks.is_owner()
    async def report_channel(
        self, ctx: Context, channel: discord.TextChannel = None
    ):
        """Set reports channel"""

        if not channel:
            channel = ctx.channel
        await self.config.report_channel.set(channel.id)
        await ctx.send(f"Report channel set to {channel.mention}.")

    @commands.command(name="setprefix")
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @maintenance()
    async def _set_prefix(self, ctx: Context, *prefixes: str):
        """Set Brawlcord's server prefix(es)

        Enter prefixes as a comma separated list.
        """

        if not prefixes:
            await ctx.bot._prefix_cache.set_prefixes(
                guild=ctx.guild, prefixes=[]
            )
            await ctx.send("Server prefixes have been reset.")
            return
        prefixes = sorted(prefixes, reverse=True)
        await ctx.bot._prefix_cache.set_prefixes(
            guild=ctx.guild, prefixes=prefixes
        )
        inline_prefixes = [f"`{prefix}`" for prefix in prefixes]
        await ctx.send(
            f"Set {', '.join(inline_prefixes)} as server"
            f" {'prefix' if len(prefixes) == 1 else 'prefixes'}."
        )

    @commands.command(name="invite")
    async def _invite(self, ctx: Context):
        """Show Brawlcord's invite url"""

        # read_messages=True,
        # send_messages=True,
        # manage_messages=True,
        # embed_links=True,
        # attach_files=True,
        # external_emojis=True,
        # add_reactions=True
        perms = discord.Permissions(322624)

        try:
            data = await self.bot.application_info()
            invite_url = discord.utils.oauth_url(data.id, permissions=perms)
            value = (
                "Add Brawlcord to your server by **[clicking here]"
                f"({invite_url})**.\n\n**Note:** By using the link"
                " above, Brawlcord will be able to"
                " read messages,"
                " send messages,"
                " manage messages,"
                " embed links,"
                " attach files,"
                " add reactions,"
                " and use external emojis"
                " wherever allowed.\n\n*You can remove the permissions manually,"
                " but that may break the bot.*"
            )
        except Exception as exc:
            invite_url = None
            value = (
                f"Error \"{exc}\" while generating invite link."
                " Notify bot owner using the `-report` command."
            )

        embed = discord.Embed(color=EMBED_COLOR, description=value)
        embed.set_author(
            name=f"Invite {ctx.me.name}", icon_url=ctx.me.avatar_url)
        # embed.add_field(name="__**Invite Link:**__", value=value)

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="info", aliases=["brawlcord"])
    async def _brawlcord(self, ctx: Context):
        """Show info about Brawlcord"""

        from .brawlcord import __version__

        info = (
            "Brawlcord is a Discord bot which allows users to simulate"
            f" a simple version of [Brawl Stars]({BRAWLSTARS}), a mobile"
            f" game developed by Supercell. \n\nBrawlcord has features"
            " such as interactive 1v1 Brawls, diverse Brawlers and"
            " leaderboards! You can suggest more features in [the community"
            f" server]({COMMUNITY_SERVER})!\n\n{ctx.me.name} is currently in"
            f" **{len(self.bot.guilds)}** servers!"
        )

        disclaimer = (
            "This content is not affiliated with, endorsed, sponsored,"
            " or specifically approved by Supercell and Supercell is"
            " not responsible for it. For more information see Supercell’s"
            f" [Fan Content Policy]({FAN_CONTENT_POLICY})."
        )

        embed = discord.Embed(color=EMBED_COLOR)

        embed.add_field(name="About Brawlcord", value=info, inline=False)

        embed.add_field(name="Creator", value=f"[Snowsee]({REDDIT_LINK})")

        page = urllib.request.urlopen(BRAWLCORD_CODE_URL)

        text = page.read()

        version_str = f"[{__version__}]({SOURCE_LINK})"

        match = re.search("__version__ = \"(.+)\"", text.decode("utf-8"))

        if match:
            current_ver = match.group(1)
            if LooseVersion(current_ver) > LooseVersion(__version__):
                version_str += f" ({current_ver} is available!)"

        embed.add_field(name="Version", value=version_str)

        embed.add_field(name="Invite Link",
                        value=f"[Click here]({INVITE_URL})")

        embed.add_field(
            name="Feedback",
            value=(
                f"You can give feedback to improve Brawlcord in"
                f" [the community server]({COMMUNITY_SERVER})."
            ),
            inline=False
        )

        embed.add_field(name="Disclaimer", value=disclaimer, inline=False)

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command()
    async def support(self, ctx: Context):
        """Show bot support information."""

        txt = (
            "You can get support for the bot in the Brawlcord"
            f" community server: {COMMUNITY_SERVER}"
        )

        await ctx.send(txt)

    @commands.command(name="discord")
    async def _discord(self, ctx: Context):
        """Show a link to the community Brawlcord server"""

        await ctx.send(
            f"You can join the Brawlcord community server by using this link: {COMMUNITY_SERVER}"
        )

    @commands.command(name="license")
    async def license_(self, ctx: Context):
        """Shows's Brawlcord's license"""

        await ctx.send(
            "Brawlcord is an instance of Red-DiscordBot, which is licensed under the GNU GPLv3."
            " For more information about Red's license, use `licenseinfo` command."
            "\n\nThe source code of Brawlcord itself is available under the MIT license."
            " The full text of the license is available at"
            " <https://github.com/brawlcord/brawlcord/blob/release/LICENSE>"
        )

    @commands.command(name="credits")
    async def _credits(self, ctx: Context):
        """Display credits"""

        credits_ = (
            "Brawlcord would not have existed without the following:"
            "\n\n- [Supercell](https://supercell.com/en/)"
            "\n - [Red](https://github.com/Cog-Creators/Red-DiscordBot)"
            "\n- [Star List](https://www.starlist.pro) - Huge thanks to"
            " Henry for allowing me to use assets from his site!"
            "\n- [Brawl Stats](https://brawlstats.com) - Huge thanks to"
            " tryso for allowing me to use his artwork!"
        )

        embed = discord.Embed(
            color=EMBED_COLOR, description=credits_
        )

        embed.set_author(name="Credits")

        await ctx.send(embed=embed)

    @commands.command(name="deletedata")
    async def _delete_data(self, ctx: Context):
        """Request deletion of your account data"""

        if ctx.guild is not None:
            return await ctx.send("This command is available in DMs only.")

        msg = await ctx.send(
            "Are you sure you want to delete all your data? It will reset"
            " all your progress. **This action is irreversible.**"
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await ctx.bot.wait_for("reaction_add", check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to react. Data deletion cancelled.")

        if pred.result is True:
            await ctx.send(
                "Please reply to this message by sending `CONFIRM`,"
                " without any formatting, to confirm data deletion."
            )

            inner_pred = MessagePredicate.same_context(ctx)

            try:
                await self.bot.wait_for("message", check=inner_pred, timeout=30)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long to respond. Data deletion cancelled.")

            if inner_pred.content.strip() == "CONFIRM":
                await self.config.user(ctx.author).clear()
            else:
                return await ctx.send("Cancelled data deletion.")

        else:
            return await ctx.send("Cancelled data deletion request.")

        await ctx.send(
            "Data deletion request successful. All data associated with your account"
            " will be deleted within 24 hours. Data is not recoverable anymore."
        )

    @commands.command(name="getdata")
    @commands.cooldown(rate=1, per=21600, type=commands.BucketType.user)
    async def _get_data(self, ctx: Context):
        """DM a `json` file with all your data.

        You can request data once every 6 hours.
        """

        data = await self.config.user(ctx.author).all()

        data_json = json.dumps(data)

        file = text_to_file(data_json, filename=f"{ctx.author.name.lower()}_brawlcord_data.json")

        try:
            await ctx.author.send(file=file)
        except discord.Forbidden:
            await ctx.send("Unable to DM you.")

        await ctx.send("Sent you the file!")
