import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils.chat_formatting import pagify

from .abc import MixinMeta
from .utils.box import Box
from .utils.constants import EMBED_COLOR
from .utils.cooldown import user_cooldown, user_cooldown_msg
from .utils.core import maintenance
from .utils.emojis import emojis

DAY = 86400
WEEK = 604800


class EconomyMixin(MixinMeta):
    """Class for all economy commands."""

    @commands.command(name="brawlbox", aliases=['box'])
    @maintenance()
    async def _brawl_box(self, ctx: Context):
        """Open a Brawl Box using Tokens"""

        user = ctx.author

        tokens = await self.get_player_stat(user, 'tokens')

        if tokens < 100:
            return await ctx.send(
                "You do not have enough Tokens to open a brawl box."
            )

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.brawlbox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(
                f"Error \"{exc}\" while opening a Brawl Box."
                " Please notify bot creator using `-report` command."
            )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

        await self.update_player_stat(user, 'tokens', -100, add_self=True)

    @commands.command(name="bigbox", aliases=['big'])
    @maintenance()
    async def _big_box(self, ctx: Context):
        """Open a Big Box using Star Tokens"""

        user = ctx.author

        startokens = await self.get_player_stat(user, 'startokens')

        if startokens < 10:
            return await ctx.send(
                "You do not have enough Star Tokens to open a brawl box."
            )

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.bigbox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(
                f"Error {exc} while opening a Big Box."
                " Please notify bot creator using `-report` command."
            )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

        await self.update_player_stat(user, 'startokens', -10, add_self=True)

    @commands.group(name="rewards", aliases=["trophyroad", "tr"])
    @maintenance()
    async def _rewards(self, ctx: Context):
        """View and claim collected trophy road rewards"""
        pass

    @_rewards.command(name="list")
    async def rewards_list(self, ctx: Context):
        """View collected trophy road rewards"""

        user = ctx.author

        tpstored = await self.get_player_stat(user, 'tpstored')

        desc = (
            "Use `-rewards claim <reward_number>` or"
            " `-rewards claimall` to claim rewards!"
        )
        embed = discord.Embed(
            color=EMBED_COLOR, title="Rewards List", description=desc)
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        embed_str = ""

        for tier in tpstored:
            reward_data = self.TROPHY_ROAD[tier]
            reward_name, reward_emoji, reward_str = self.tp_reward_strings(
                reward_data, tier)

            embed_str += (
                f"\n**{tier}.** {reward_name}: {reward_emoji} {reward_str}"
            )

        if embed_str:
            embed.add_field(name="Rewards", value=embed_str.strip())
        else:
            embed.add_field(
                name="Rewards", value="You don't have any rewards.")

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @_rewards.command(name="all")
    async def rewards_all(self, ctx: Context):
        """View all trophy road rewards."""

        user = ctx.author

        tpstored = await self.get_player_stat(user, 'tpstored')
        tppassed = await self.get_player_stat(user, 'tppassed')
        trophies = await self.get_trophies(user)

        tr_str = ""
        desc = f"You have {trophies} {emojis['trophies']} at the moment."

        embeds = []

        max_tier = max(tppassed, key=lambda m: int(m))
        max_trophies = self.TROPHY_ROAD[max_tier]['Trophies']

        for tier in self.TROPHY_ROAD:
            reward_data = self.TROPHY_ROAD[tier]
            reward_name, reward_emoji, reward_str = self.tp_reward_strings(reward_data, tier)

            if tier in tpstored:
                extra = " **(Can Claim!)**"
            elif tier in tppassed:
                extra = " **(Claimed!)**"
            else:
                extra = ""

            tr_str += (
                f"\n\n{emojis['trophies']} **{reward_data['Trophies']}** -"
                f" {reward_name}: {reward_emoji} {reward_str}{extra}"
            )

        pages = list(pagify(tr_str, page_length=1000))
        total_pages = len(pages)

        start_at = 0

        for num, page in enumerate(pages, start=1):
            if f"**{max_trophies}**" in page:
                start_at = num - 1

            embed = discord.Embed(
                color=EMBED_COLOR, description=desc
            )

            embed.add_field(name="\u200b", value=page)

            embed.set_author(
                name=f"{user.name}'s Trophy Road Progress", icon_url=user.avatar_url
            )

            embed.set_footer(text=f"Page {num} of {total_pages}")

            embeds.append(embed)

        try:
            await menu(ctx, embeds, DEFAULT_CONTROLS, page=start_at)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @_rewards.command(name="claim")
    async def rewards_claim(self, ctx: Context, reward_number: str):
        """Claim collected trophy road reward"""

        user = ctx.author

        tpstored = await self.get_player_stat(user, 'tpstored')

        if reward_number not in tpstored:
            return await ctx.send(
                f"You do not have {reward_number} collected."
            )

        await self.handle_reward_claims(ctx, reward_number)

        await ctx.send("Reward successfully claimed.")

    @_rewards.command(name="claimall")
    async def rewards_claim_all(self, ctx: Context):
        """Claim all collected trophy road rewards"""
        user = ctx.author

        tpstored = await self.get_player_stat(user, 'tpstored')

        for tier in tpstored:
            await self.handle_reward_claims(ctx, str(tier))

        await ctx.send("Rewards successfully claimed.")

    @commands.group(name="claim")
    @maintenance()
    async def _claim(self, ctx: Context):
        """Claim daily/weekly rewards"""
        pass

    @_claim.command(name="daily")
    async def claim_daily(self, ctx: Context):
        """Claim daily reward"""

        if not await user_cooldown(1, DAY, self.config, ctx):
            msg = await user_cooldown_msg(ctx, self.config)
            return await ctx.send(msg)

        user = ctx.author

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.brawlbox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(
                f"Error \"{exc}\" while opening a Brawl Box."
                " Please notify bot creator using `-report` command."
            )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @_claim.command(name="weekly")
    async def claim_weekly(self, ctx: Context):
        """Claim weekly reward"""

        if not await user_cooldown(1, WEEK, self.config, ctx):
            msg = await user_cooldown_msg(ctx, self.config)
            return await ctx.send(msg)

        user = ctx.author

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.bigbox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(
                f"Error \"{exc}\" while opening a Big Box."
                " Please notify bot creator using `-report` command."
            )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.group(name="gift")
    @maintenance()
    async def _gifted(self, ctx: Context):
        """View and collect gifted Brawl, Big or Mega boxes"""
        pass

    @_gifted.command(name="list")
    async def _gifted_list(self, ctx: Context):
        """View gifted rewards"""

        user = ctx.author

        gifts = await self.get_player_stat(user, 'gifts')

        desc = "Use `-gift` command to learn more about claiming rewards!"
        embed = discord.Embed(
            color=EMBED_COLOR, title="Gifted Rewards List", description=desc)
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        embed_str = ""

        for gift_type in gifts:
            if gift_type in ["brawlbox", "bigbox", "megabox"]:
                count = gifts[gift_type]
                emoji = emojis[gift_type]
                if count > 0:
                    embed_str += (
                        f"\n{emoji} {self._box_name(gift_type)}:"
                        f" x**{count}**"
                    )
            else:
                continue

        if embed_str:
            embed.add_field(name="Rewards", value=embed_str.strip())
        else:
            embed.add_field(name="Rewards", value="You don't have any gifts.")

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @_gifted.command(name="mega")
    async def _gifted_mega(self, ctx: Context):
        """Open a gifted Mega Box, if saved"""

        user = ctx.author

        saved = await self.get_player_stat(
            user, "gifts", is_iter=True, substat="megabox")

        if saved < 1:
            return await ctx.send("You do not have any gifted mega boxes.")

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.megabox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(
                f"Error \"{exc}\" while opening a Mega Box."
                " Please notify bot creator using `-report` command."
            )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

        # await self.update_player_stat(user, 'tokens', -100, add_self=True)
        await self.update_player_stat(
            user, "gifts", -1, substat="megabox", add_self=True
        )
