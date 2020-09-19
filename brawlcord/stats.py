import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils.chat_formatting import pagify

from .abc import MixinMeta
from .utils.box import Box
from .utils.brawlers import brawler_thumb
from .utils.constants import EMBED_COLOR
from .utils.core import maintenance
from .utils.emojis import (
    brawler_emojis, emojis, gamemode_emotes, level_emotes, rank_emojis, sp_icons
)
from .utils.gamemodes import gamemodes_map


class StatisticsMixin(MixinMeta):
    """Class for all stat related commands."""

    @commands.command(name="stats", aliases=["stat"])
    @maintenance()
    async def _stats(self, ctx: Context):
        """Display your resource statistics"""

        user = ctx.author

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(
            name=f"{user.name}'s Resource Stats", icon_url=user.avatar_url)

        trophies = await self.get_trophies(user)
        embed.add_field(name="Trophies",
                        value=f"{emojis['trophies']} {trophies:,}")

        pb = await self.get_trophies(user=user, pb=True)
        embed.add_field(name="Highest Trophies",
                        value=f"{emojis['pb']} {pb:,}")

        user_data = await self.config.user(user).all()

        xp = user_data['xp']
        lvl = user_data['lvl']
        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        embed.add_field(name="Experience Level",
                        value=f"{emojis['xp']} {lvl} `{xp}/{next_xp}`")

        gold = user_data['gold']
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}")

        tokens = user_data['tokens']
        embed.add_field(name="Tokens", value=f"{emojis['token']} {tokens}")

        token_bank = user_data['tokens_in_bank']
        embed.add_field(
            name="Tokens In Bank", value=f"{emojis['token']} {token_bank}"
        )

        startokens = user_data['startokens']
        embed.add_field(name="Star Tokens",
                        value=f"{emojis['startoken']} {startokens}")

        token_doubler = user_data['token_doubler']
        embed.add_field(name="Token Doubler",
                        value=f"{emojis['tokendoubler']} {token_doubler}")

        gems = user_data['gems']
        embed.add_field(name="Gems", value=f"{emojis['gem']} {gems}")

        starpoints = user_data['starpoints']
        embed.add_field(name="Star Points",
                        value=f"{emojis['starpoints']} {starpoints}")

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="profile", aliases=["p", "pro"])
    @maintenance()
    async def _profile(self, ctx: Context, user: discord.User = None):
        """Display your or specific user's profile"""

        if not user:
            user = ctx.author

        user_data = await self.config.user(user).all()

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name=f"{user.name}'s Profile",
                         icon_url=user.avatar_url)

        trophies = await self.get_trophies(user)
        league_number, league_emoji = await self.get_league_data(trophies)
        if league_number:
            extra = f"`{league_number}`"
        else:
            extra = ""
        embed.add_field(name="Trophies",
                        value=f"{league_emoji}{extra} {trophies:,}")

        pb = await self.get_trophies(user=user, pb=True)
        embed.add_field(name="Highest Trophies",
                        value=f"{emojis['pb']} {pb:,}")

        xp = user_data['xp']
        lvl = user_data['lvl']
        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        embed.add_field(name="Experience Level",
                        value=f"{emojis['xp']} {lvl} `{xp}/{next_xp}`")

        brawl_stats = user_data['brawl_stats']

        wins_3v3 = brawl_stats["3v3"][0]
        wins_solo = brawl_stats["solo"][0]
        wins_duo = brawl_stats["duo"][0]

        embed.add_field(name="3 vs 3 Wins", value=f"{emojis['3v3']} {wins_3v3}")
        embed.add_field(
            name="Solo Wins",
            value=f"{gamemode_emotes['Solo Showdown']} {wins_solo}"
        )
        embed.add_field(
            name="Duo Wins",
            value=f"{gamemode_emotes['Duo Showdown']} {wins_duo}"
        )

        selected = user_data['selected']
        brawler = selected['brawler']
        sp = selected['starpower']
        skin = selected['brawler_skin']
        gamemode = selected['gamemode']

        # el primo skins appear as El Rudo, Primo, etc
        if brawler == "El Primo":
            if skin != "Default":
                _brawler = "Primo"
            else:
                _brawler = brawler
        else:
            _brawler = brawler

        embed.add_field(
            name="Selected Brawler",
            value=(
                "{} {} {} {}".format(
                    brawler_emojis[brawler],
                    skin if skin != "Default" else "",
                    _brawler,
                    f" - {emojis['spblank']} {sp}" if sp else ""
                )
            ),
            inline=False
        )
        embed.add_field(
            name="Selected Game Mode",
            value=f"{gamemode_emotes[gamemode]} {gamemode}",
            inline=False
        )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="brawlers", aliases=['brls'])
    @maintenance()
    async def all_owned_brawlers(
        self, ctx: Context, user: discord.User = None
    ):
        """Show details of all the Brawlers you own"""

        if not user:
            user = ctx.author

        owned = await self.get_player_stat(user, 'brawlers', is_iter=True)

        def create_embed(new=False):
            embed = discord.Embed(color=EMBED_COLOR)
            if not new:
                embed.set_author(name=f"{user.name}'s Brawlers")

            return embed

        embeds = [create_embed()]

        # below code is to sort brawlers by their trophies
        brawlers = {}
        for brawler in owned:
            brawlers[brawler] = owned[brawler]["trophies"]

        sorted_brawlers = dict(
            sorted(brawlers.items(), key=lambda x: x[1], reverse=True))

        for brawler in sorted_brawlers:
            level = owned[brawler]["level"]
            trophies = owned[brawler]["trophies"]
            pb = owned[brawler]["pb"]
            rank = owned[brawler]["rank"]
            skin = owned[brawler]["selected_skin"]

            if skin == "Default":
                skin = ""
            else:
                skin += " "

            if brawler == "El Primo":
                if skin != "Default":
                    _brawler = "Primo"
            else:
                _brawler = brawler

            emote = level_emotes["level_" + str(level)]

            value = (f"{emote}`{trophies:>4}` {rank_emojis['br'+str(rank)]} |"
                     f" {emojis['powerplay']}`{pb:>4}`")

            for i, embed in enumerate(embeds):
                if len(embed.fields) == 25:
                    if i == len(embeds) - 1:
                        embed = create_embed(new=True)
                        embeds.append(embed)
                        break

            embed.add_field(
                name=(
                    f"{brawler_emojis[brawler]} {skin.upper()}"
                    f"{_brawler.upper()}"
                ),
                value=value,
                inline=False
            )

        for embed in embeds:
            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                return await ctx.send(
                    "I do not have the permission to embed a link."
                    " Please give/ask someone to give me that permission."
                )

    @commands.command(name="upgrades")
    @maintenance()
    async def _upgrades(self, ctx: Context):
        """Show Brawlers which can be upgraded"""

        user = ctx.author

        user_owned = await self.get_player_stat(user, 'brawlers', is_iter=True)

        embed_str = ""

        idx = 1
        for brawler in user_owned:
            brawler_data = await self.get_player_stat(
                user, 'brawlers', is_iter=True, substat=brawler)

            level = brawler_data['level']
            if level >= 9:
                continue

            powerpoints = brawler_data['powerpoints']

            required_powerpoints = self.LEVEL_UPS[str(level)]["Progress"]

            required_gold = self.LEVEL_UPS[str(level)]["RequiredCurrency"]

            if powerpoints >= required_powerpoints:
                embed_str += (
                    f"\n{idx}. {brawler} {brawler_emojis[brawler]} ({level}"
                    f" -> {level+1}) - {emojis['gold']} {required_gold}"
                )
                idx += 1

        embeds = []
        if embed_str:
            gold = await self.get_player_stat(user, 'gold')
            desc = (
                "The following Brawlers can be upgraded by using the"
                " `-upgrade <brawler_name>` command."
                f"\n\nAvailable Gold: {emojis['gold']} {gold}"
            )
            pages = list(pagify(text=embed_str, page_length=1000))
            total = len(pages)
            for i, page in enumerate(pages, start=1):
                embed = discord.Embed(
                    color=EMBED_COLOR,
                    description=desc,
                    timestamp=ctx.message.created_at
                )
                embed.set_author(
                    name=f"{user.name}'s Upgradable Brawlers",
                    icon_url=user.avatar_url
                )
                embed.set_footer(text=f"Page {i}/{total}")
                embed.add_field(name="Upgradable Brawlers", value=page)
                embeds.append(embed)
        else:
            embed = discord.Embed(
                color=EMBED_COLOR,
                description="You can't upgrade any Brawler at the moment."
            )
            embed.set_author(
                name=f"{user.name}'s Upgradable Brawlers",
                icon_url=user.avatar_url
            )
            embeds.append(embed)

        await menu(ctx, embeds, DEFAULT_CONTROLS)

    @commands.command(name="powerpoints", aliases=['pps'])
    @maintenance()
    async def _powerpoints(self, ctx: Context):
        """Show number of power points each Brawler has"""

        user = ctx.author

        user_owned = await self.get_player_stat(user, 'brawlers', is_iter=True)

        embed_str = ""

        for brawler in user_owned:
            brawler_data = await self.get_player_stat(
                user, 'brawlers', is_iter=True, substat=brawler)

            level = brawler_data['level']
            level_emote = level_emotes["level_" + str(level)]

            if level < 9:
                powerpoints = brawler_data['powerpoints']

                required_powerpoints = self.LEVEL_UPS[str(level)]["Progress"]

                embed_str += (
                    f"\n{level_emote} {brawler} {brawler_emojis[brawler]}"
                    f" - {powerpoints}/{required_powerpoints}"
                    f" {emojis['powerpoint']}"
                )

            else:
                sp1 = brawler_data['sp1']
                sp2 = brawler_data['sp2']

                if sp1:
                    sp1_icon = sp_icons[brawler][0]
                else:
                    sp1_icon = emojis['spgrey']
                if sp2:
                    sp2_icon = sp_icons[brawler][1]
                else:
                    sp2_icon = emojis['spgrey']

                embed_str += (
                    f"\n{level_emote} {brawler} {brawler_emojis[brawler]}"
                    f" - {sp1_icon} {sp2_icon}"
                )

        embeds = []
        # embed.add_field(name="Brawlers", value=embed_str)

        pages = list(pagify(text=embed_str))
        total = len(pages)
        for i, page in enumerate(pages, start=1):
            embed = discord.Embed(
                color=EMBED_COLOR,
                description=page,
                timestamp=ctx.message.created_at
            )

            embed.set_author(
                name=f"{user.name}'s Power Points Info",
                icon_url=user.avatar_url
            )
            embed.set_footer(text=f"Page {i}/{total}")
            embeds.append(embed)

        try:
            await menu(ctx, embeds, DEFAULT_CONTROLS)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="skins")
    @maintenance()
    async def _skins(self, ctx: Context):
        """View all skins you own"""

        brawler_data = await self.get_player_stat(
            ctx.author, 'brawlers', is_iter=True
        )

        embed = discord.Embed(
            colour=EMBED_COLOR
        )
        embed.set_author(
            name=f"{ctx.author.name}'s Skins", icon_url=ctx.author.avatar_url
        )

        total = 0
        for brawler in brawler_data:
            skins = brawler_data[brawler]["skins"]
            if len(skins) < 2:
                continue
            brawler_skins = ""
            for skin in skins:
                if skin == "Default":
                    continue
                brawler_skins += f"\n- {skin} {brawler}"
                total += 1
            embed.add_field(
                name=f"{brawler_emojis[brawler]} {brawler} ({len(skins)-1})",
                value=brawler_skins,
                inline=False
            )

        embed.set_footer(text=f"Total Skins: {total}")

        await ctx.send(embed=embed)

    @commands.command(name="startokens")
    @maintenance()
    async def _star_tokens(self, ctx: Context):
        """Show details of today's star tokens"""

        todays_st = await self.config.user(ctx.author).todays_st()

        user_gamemodes = await self.config.user(ctx.author).gamemodes()

        collected = ""
        not_collected = ""

        for gamemode in user_gamemodes:
            if gamemode not in gamemodes_map:
                continue
            if gamemode in todays_st:
                collected += f"\n{gamemode_emotes[gamemode]} {gamemode}"
            else:
                not_collected += f"\n{gamemode_emotes[gamemode]} {gamemode}"

        embed = discord.Embed(
            colour=EMBED_COLOR
        )
        if collected:
            embed.add_field(name="Collected", value=collected)
        if not_collected:
            embed.add_field(name="Not Collected", value=not_collected)

        await ctx.send(embed=embed)

    @commands.group(
        name="leaderboard",
        aliases=['lb'],
        autohelp=False,
        usage='[brawler or pb] [brawler_name]'
    )
    @maintenance()
    async def _leaderboard(self, ctx: Context, arg: str = None, extra: str = None):
        """Display the leaderboard"""

        if not ctx.invoked_subcommand:
            if arg:
                if arg.lower() == 'pb':
                    pb = self.bot.get_command('leaderboard pb')
                    return await ctx.invoke(pb)
                elif arg.lower() == 'brawler':
                    lb_brawler = self.bot.get_command('leaderboard brawler')
                    if not extra:
                        return await ctx.send_help(lb_brawler)
                    else:
                        return await ctx.invoke(lb_brawler, brawler_name=extra)
                else:
                    brawler = self.parse_brawler_name(arg)
                    if brawler:
                        lb_brawler = self.bot.get_command('leaderboard brawler')
                        return await ctx.invoke(lb_brawler, brawler_name=brawler)

            title = "Brawlcord Leaderboard"

            url = "https://www.starlist.pro/assets/icon/trophy.png"

            await self.leaderboard_handler(ctx, title, url, 5)

    @_leaderboard.command(name="pb")
    async def pb_leaderboard(self, ctx: Context):
        """Display the personal best leaderboard"""

        title = "Brawlcord Leaderboard - Highest Trophies"

        url = "https://www.starlist.pro/assets/icon/trophy.png"

        await self.leaderboard_handler(ctx, title, url, 5, pb=True)

    @_leaderboard.command(name="brawler")
    async def brawler_leaderboard(self, ctx: Context, *, brawler_name: str):
        """Display the specified brawler's leaderboard"""

        brawler = self.parse_brawler_name(brawler_name)

        if not brawler:
            return await ctx.send(f"{brawler_name} does not exist!")

        title = f"Brawlcord {brawler} Leaderboard"

        url = f"{brawler_thumb.format(brawler)}"

        await self.leaderboard_handler(
            ctx, title, url, 4, brawler_name=brawler
        )

    @commands.command()
    @maintenance()
    async def drops(self, ctx: Context):
        """Show Brawl Box drop rates"""

        brawler_data = await self.get_player_stat(
            ctx.author, "brawlers", is_iter=True
        )

        box = Box(self.BRAWLERS, brawler_data)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name="Drop Rates", icon_url=ctx.author.avatar_url)

        def get_value_str(value: int):
            return f"{value}%"

        # TODO: Add emojis in front of values before release
        embed.add_field(name="Power Points", value=get_value_str(box.powerpoint))
        embed.add_field(name="Rare Brawler", value=get_value_str(box.rare))
        embed.add_field(name="Super Rare Brawler", value=get_value_str(box.superrare))
        embed.add_field(name="Epic Brawler", value=get_value_str(box.epic))
        embed.add_field(name="Mythic Brawler", value=get_value_str(box.mythic))
        embed.add_field(name="Legendary Brawler", value=get_value_str(box.legendary))
        embed.add_field(name="Gems", value=get_value_str(box.gems))
        embed.add_field(name="Tickets", value=get_value_str(box.tickets))
        embed.add_field(name="Token Doubler", value=get_value_str(box.td))

        await ctx.send(embed=embed)
