import asyncio
import random
import traceback
from datetime import datetime

import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu, start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from .abc import MixinMeta
from .utils.battlelog import BattleLogEntry
from .utils.brawlers import Brawler, brawlers_map
from .utils.club import Club
from .utils.constants import COMMUNITY_SERVER, EMBED_COLOR, SHELLY_TUT
from .utils.core import maintenance
from .utils.emojis import brawler_emojis, club_icons, emojis, gamemode_emotes, level_emotes
from .utils.errors import AmbiguityError, UserRejected
from .utils.gamemodes import GameMode, gamemodes_map
from .utils.shop import Shop

LOG_COLORS = {
    "Victory": 0x6CFF52,
    "Loss": 0xFF5B5B,
    "Draw": EMBED_COLOR
}

gamemode_thumb = "https://www.starlist.pro/assets/gamemode/{}.png"


class GameplayMixin(MixinMeta):
    """Class for gameplay commands."""

    @commands.command(name="brawl", aliases=["b", "play"])
    @commands.guild_only()
    @maintenance()
    async def _brawl(self, ctx: Context, *, opponent: discord.Member = None):
        """Brawl against other players"""

        guild = ctx.guild
        user = ctx.author

        tutorial_finished = await self.get_player_stat(
            user, 'tutorial_finished'
        )

        if not tutorial_finished:
            return await ctx.send(
                "You have not finished the tutorial yet."
                " Please use the `-tutorial` command to proceed."
            )

        if opponent:
            if opponent == user:
                return await ctx.send("You can't brawl against yourself.")
            elif opponent == guild.me:
                pass
            # don't allow brawl if opponent is another bot
            elif opponent.bot:
                return await ctx.send(
                    f"{opponent} is a bot account. Can't brawl against bots.")

        if user.id in self.sessions:
            return await ctx.send("You are already in a brawl!")

        if opponent:
            if opponent.id in self.sessions:
                return await ctx.send(f"{opponent} is already in a brawl!")

            if opponent != guild.me:
                self.sessions.append(opponent.id)

        self.sessions.append(user.id)

        gm = await self.get_player_stat(
            user, "selected", is_iter=True, substat="gamemode"
        )

        g: GameMode = gamemodes_map[gm](
            ctx, user, opponent, self.config.user, self.BRAWLERS)

        await ctx.send(f"Please check your Direct Messages.")

        try:
            first_player, second_player = await g.initialize(ctx)
            winner, loser = await g.play(ctx)
        except (asyncio.TimeoutError, UserRejected, discord.Forbidden):
            return
        except Exception as exc:
            traceback.print_tb(exc.__traceback__)
            return await ctx.send(
                f"Error: \"{exc}\" with brawl."
                " Please notify bot owner by using `-report` command."
            )
        finally:
            self.sessions.remove(user.id)
            try:
                self.sessions.remove(opponent.id)
            except (ValueError, AttributeError):
                pass

        players = [first_player, second_player]

        if winner:
            await ctx.send(
                f"{first_player.mention} {second_player.mention}"
                f" Match ended. Winner: {winner.name}!"
            )
        else:
            await ctx.send(
                f"{first_player.mention} {second_player.mention}"
                " The match ended in a draw!"
            )

        log_data = []
        count = 0
        for player in players:
            if player == guild.me:
                continue
            if player == winner:
                points = 1
            elif player == loser:
                points = -1
            else:
                points = 0

            # brawl rewards, rank up rewards and trophy road rewards
            br, rur, trr = await self.brawl_rewards(player, points, gm)

            log_data.append({"user": player, "trophies": br[1], "reward": br[2]})

            count += 1
            if count == 1:
                await ctx.send("Direct messaging rewards!")
            level_up = await self.xp_handler(player)
            await player.send(embed=br[0])
            if level_up:
                await player.send(f"{level_up[0]}\n{level_up[1]}")
            if rur:
                await player.send(embed=rur)
            if trr:
                await player.send(embed=trr)

        await self.save_battle_log(log_data)

    @commands.command(name="tutorial", aliases=["tut"])
    @commands.guild_only()
    @maintenance()
    async def _tutorial(self, ctx: Context):
        """Begin the tutorial"""

        author = ctx.author

        finished_tutorial = await self.get_player_stat(
            author, "tutorial_finished")

        if finished_tutorial:
            return await ctx.send(
                "You have already finished the tutorial."
                " It's time to test your skills in the real world!"
            )

        desc = ("Hi, I'm Shelly! I'll introduce you to the world of Brawlcord."
                " Don't worry Brawler, it will only take a minute!")

        embed = discord.Embed(
            color=EMBED_COLOR, title="Tutorial", description=desc)
        # embed.set_author(name=author, icon_url=author_avatar)
        embed.set_thumbnail(url=SHELLY_TUT)

        tut_str = (
            f"This {emojis['gem']} is a Gem. All the gems are mine!"
            " Gotta collect them all!"
            "\n\nTo collect the gems, you need to take part in the dreaded"
            " Brawls! Use `-brawl`"
            " command after this tutorial ends to brawl!"
            f"\n\nYou win a brawl by collecting 10 Gems before your opponent."
            " But be cautious!"
            " If the opponent manages to defeat you, you will lose about half"
            " of your gems!"
            " Remember, you can dodge the opponent's attacks. You can also"
            " attack the opponent!"
            "\n\nYou earn Tokens by participating in a brawl. Use the Tokens"
            " to open Brawl Boxes."
            "  They contain goodies that allow you increase your strength and"
            " even other Brawlers!"
            "\n\nYou can keep a track of your resources by using the `-stats`."
            " You can view your"
            " brawl statistics by using the `-profile` command."
            "\n\nYou can always check all the commands again by using the"
            " `-help` command."
            f"\n\nThat's all, {author.mention}. You're a natural Brawler! Now,"
            " let's go get 'em!"
        )

        embed.add_field(name="__Introduction:__", value=tut_str, inline=False)

        embed.add_field(
            name="\u200b\n__Feedback:__",
            value=(
                "You can give feedback to improve Brawlcord in the"
                f" [Brawlcord community server]({COMMUNITY_SERVER})."
            ),
            inline=False
        )

        embed.set_footer(text="Thanks for using Brawlcord.", icon_url=ctx.me.avatar_url)

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

        await self.update_player_stat(author, 'tutorial_finished', True)

        dt_now = datetime.utcnow()
        epoch = datetime(1970, 1, 1)
        # get timestamp in UTC
        timestamp = (dt_now - epoch).total_seconds()
        await self.update_player_stat(author, 'bank_update_ts', timestamp)

    @commands.command(name="brawler", aliases=['binfo'])
    @maintenance()
    async def _brawler(self, ctx: Context, *, brawler_name: str):
        """Show stats of a particular Brawler"""

        user = ctx.author

        brawlers = self.BRAWLERS

        # for users who input 'el_primo' or 'primo'
        brawler_name = brawler_name.replace("_", " ")
        if brawler_name.lower() in "el primo":
            brawler_name = "El Primo"

        brawler_name = brawler_name.title()

        for brawler in brawlers:
            if brawler_name in brawler:
                break
            else:
                brawler = None

        if not brawler:
            return await ctx.send(f"{brawler_name} does not exist.")

        owned_brawlers = await self.get_player_stat(
            user, 'brawlers', is_iter=True)

        owned = True if brawler in owned_brawlers else False

        b: Brawler = brawlers_map[brawler](self.BRAWLERS, brawler)

        if owned:
            brawler_data = await self.get_player_stat(
                user, 'brawlers', is_iter=True, substat=brawler)
            pp = brawler_data['powerpoints']
            trophies = brawler_data['trophies']
            rank = brawler_data['rank']
            level = brawler_data['level']
            if level < 9:
                next_level_pp = self.LEVEL_UPS[str(level)]["Progress"]
            else:
                next_level_pp = 0
                pp = 0
            pb = brawler_data['pb']
            sp1 = brawler_data['sp1']
            sp2 = brawler_data['sp2']

            embed = b.brawler_info(brawler, trophies, pb,
                                   rank, level, pp, next_level_pp, sp1, sp2)

        else:
            embed = b.brawler_info(brawler)

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="allbrawlers", aliases=['abrawlers', 'abrls'])
    @maintenance()
    async def all_brawlers(self, ctx: Context):
        """Show list of all the Brawlers"""

        owned = await self.get_player_stat(
            ctx.author, 'brawlers', is_iter=True)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name="All Brawlers")

        rarities = ["Trophy Road", "Rare",
                    "Super Rare", "Epic", "Mythic", "Legendary"]
        for rarity in rarities:
            rarity_str = ""
            for brawler in self.BRAWLERS:
                if rarity != self.BRAWLERS[brawler]["rarity"]:
                    continue
                rarity_str += f"\n{brawler_emojis[brawler]} {brawler}"
                if brawler in owned:
                    rarity_str += " [Owned]"

            if rarity_str:
                embed.add_field(name=rarity, value=rarity_str, inline=False)

        embed.set_footer(
            text=f"Owned: {len(owned)} | Total: {len(self.BRAWLERS)}")

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="gamemodes", aliases=['gm', 'events'])
    @maintenance()
    async def _gamemodes(self, ctx: Context):
        """Show details of all the game modes"""

        user = ctx.author

        user_owned = await self.get_player_stat(
            user, 'gamemodes', is_iter=True)

        embed = discord.Embed(color=EMBED_COLOR, title="Game Modes")
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        for event_type in [
            "Team Event", "Solo Event", "Duo Event", "Ticket Event"
        ]:
            embed_str = ""
            for gamemode in self.GAMEMODES:
                if event_type != self.GAMEMODES[gamemode]["event_type"]:
                    continue
                embed_str += f"\n{gamemode_emotes[gamemode]} {gamemode}"
                if gamemode not in user_owned:
                    embed_str += f" [Locked]"

            embed.add_field(name=event_type + "s", value=embed_str, inline=False)

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    @commands.command(name="upgrade", aliases=['up'])
    @maintenance()
    async def upgrade_brawlers(self, ctx: Context, *, brawler: str):
        """Upgrade a Brawler"""

        user = ctx.author

        user_owned = await self.get_player_stat(user, 'brawlers', is_iter=True)

        if self.parse_brawler_name(brawler):
            brawler = self.parse_brawler_name(brawler)

        if brawler not in user_owned:
            return await ctx.send(f"You do not own {brawler}!")

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True, substat=brawler)
        level = brawler_data['level']
        if level == 9:
            return await ctx.send(
                "Brawler is already at level 9. Open"
                " boxes to collect Star Powers!"
            )
        elif level == 10:
            return await ctx.send(
                "Brawler is already at level 10. If you are"
                " missing a Star Power, then open boxes to collect it!"
            )

        powerpoints = brawler_data['powerpoints']

        required_powerpoints = self.LEVEL_UPS[str(level)]["Progress"]

        if powerpoints < required_powerpoints:
            return await ctx.send(
                "You do not have enough powerpoints!"
                f" ({powerpoints}/{required_powerpoints})"
            )

        gold = await self.get_player_stat(user, 'gold', is_iter=False)

        required_gold = self.LEVEL_UPS[str(level)]["RequiredCurrency"]

        if gold < required_gold:
            return await ctx.send(
                f"You do not have enough gold! ({gold}/{required_gold})"
            )

        msg = await ctx.send(
            f"{user.mention} Upgrading {brawler} to power {level+1}"
            f" will cost {emojis['gold']} {required_gold}. Continue?"
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result:
            # User responded with tick
            pass
        else:
            # User responded with cross
            return await ctx.send("Upgrade cancelled.")

        await self.update_player_stat(
            user, 'brawlers', level + 1, substat=brawler, sub_index='level')
        await self.update_player_stat(
            user, 'brawlers', powerpoints - required_powerpoints,
            substat=brawler, sub_index='powerpoints'
        )
        await self.update_player_stat(user, 'gold', gold - required_gold)

        await ctx.send(f"Upgraded {brawler} to power {level+1}!")

    @commands.group(name="select")
    @maintenance()
    async def _select(self, ctx: Context):
        """Change selected Brawler, skin, star power or game mode"""
        pass

    @_select.command(name="brawler")
    async def select_brawler(self, ctx: Context, *, brawler_name: str):
        """Change selected Brawler"""

        user_owned = await self.get_player_stat(
            ctx.author, 'brawlers', is_iter=True)

        # for users who input 'el_primo'
        brawler_name = brawler_name.replace("_", " ")

        brawler_name = brawler_name.title()

        if brawler_name not in user_owned:
            return await ctx.send(f"You do not own {brawler_name}!")

        await self.update_player_stat(
            ctx.author, 'selected', brawler_name, substat='brawler')

        brawler_data = await self.get_player_stat(
            ctx.author, 'brawlers', is_iter=True, substat=brawler_name)

        sps = [f"sp{ind}" for ind, sp in enumerate(
            [brawler_data["sp1"], brawler_data["sp2"]], start=1) if sp]
        sps = [self.BRAWLERS[brawler_name][sp]["name"] for sp in sps]

        if sps:
            await self.update_player_stat(
                ctx.author, 'selected', random.choice(sps),
                substat='starpower'
            )
        else:
            await self.update_player_stat(
                ctx.author, 'selected', None, substat='starpower')

        skin = brawler_data["selected_skin"]
        await self.update_player_stat(
            ctx.author, 'selected', skin, substat='brawler_skin')

        await ctx.send(f"Changed selected Brawler to {brawler_name}!")

    @_select.command(name="gamemode", aliases=["gm"])
    async def select_gamemode(self, ctx: Context, *, gamemode: str):
        """Change selected game mode"""

        try:
            gamemode = self.parse_gamemode(gamemode)
        except AmbiguityError as e:
            return await ctx.send(e)

        if gamemode is None:
            return await ctx.send("Unable to identify game mode.")

        if gamemode not in ["Gem Grab", "Solo Showdown", "Brawl Ball"]:
            return await ctx.send(
                "The game only supports **Gem Grab**, **Solo Showdown** and"
                " **Brawl Ball** at the moment. More game modes will be added soon!"
            )

        user_owned = await self.get_player_stat(
            ctx.author, 'gamemodes', is_iter=True
        )

        if gamemode not in user_owned:
            return await ctx.send(f"You do not own {gamemode}!")

        await self.update_player_stat(
            ctx.author, 'selected', gamemode, substat='gamemode')

        await ctx.send(f"Changed selected game mode to {gamemode}!")

    @_select.command(name="skin")
    async def select_skin(self, ctx: Context, *, skin: str):
        """Change selected skin"""

        user = ctx.author

        skin = skin.title()
        cur_skin = await self.get_player_stat(
            user, 'selected', is_iter=True, substat='brawler_skin')

        selected_brawler = await self.get_player_stat(
            user, 'selected', is_iter=True, substat='brawler')

        if skin == cur_skin:
            return await ctx.send(
                f"{skin} {selected_brawler} skin is already selected.")

        selected_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True, substat=selected_brawler)

        skins = selected_data['skins']

        if skin not in skins:
            return await ctx.send(
                f"You don't own {skin} {selected_brawler}"
                " skin or it does not exist."
            )

        await self.update_player_stat(
            user, 'selected', skin, substat='brawler_skin')
        await self.update_player_stat(
            user, 'brawlers', skin, substat=selected_brawler,
            sub_index='selected_skin'
        )

        await ctx.send(f"Changed selected skin from {cur_skin} to {skin}.")

    @_select.command(name="starpower", aliases=['sp'])
    async def select_sp(self, ctx: Context, *, starpower_number: int):
        """Change selected star power"""

        user = ctx.author

        selected_brawler = await self.get_player_stat(
            user, 'selected', is_iter=True, substat='brawler')

        sp = "sp" + str(starpower_number)
        sp_name, emote = self.get_sp_info(selected_brawler, sp)

        cur_sp = await self.get_player_stat(
            user, 'selected', is_iter=True, substat='starpower')

        if sp_name == cur_sp:
            return await ctx.send(f"{sp_name} is already selected.")

        selected_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True, substat=selected_brawler)

        if starpower_number in [1, 2]:
            if selected_data[sp]:
                await self.update_player_stat(
                    user, 'selected', sp_name, substat='starpower')
            else:
                return await ctx.send(
                    f"You don't own SP #{starpower_number}"
                    f" of {selected_brawler}."
                )
        else:
            return await ctx.send("You can only choose SP #1 or SP #2.")

        await ctx.send(f"Changed selected Star Power to {sp_name}.")

    @commands.group(name="shop")
    @maintenance()
    async def _shop(self, ctx: Context):
        """View your daily shop and buy items"""

        if not ctx.invoked_subcommand:
            await self._view_shop(ctx)

    @_shop.command(name="buy")
    @maintenance()
    async def _shop_buy(self, ctx: Context, item_number: str):
        """Buy items from the daily shop"""

        data = await self.config.user(ctx.author).shop()

        shop = Shop.from_json(data)

        try:
            item_number = int(item_number)
            new_data = await shop.buy_item(
                ctx, ctx.author, self.config, self.BRAWLERS, item_number
            )
        except ValueError:
            new_data = await shop.buy_skin(
                ctx, ctx.author, self.config,
                self.BRAWLERS, item_number.upper()
            )

        if new_data:
            await self.config.user(ctx.author).shop.set(new_data)

    @_shop.command(name="view")
    @maintenance()
    async def _shop_view(self, ctx: Context):
        """View your daily shop"""

        await self._view_shop(ctx)

    @commands.command(aliases=["log"])
    @maintenance()
    async def battlelog(self, ctx: Context):
        """Show the battle log with last 10 (or fewer) entries"""

        battle_log = await self.config.user(ctx.author).battle_log()
        battle_log.reverse()

        # Only show 10 (or fewer) most recent logs.
        battle_log = battle_log[-10:]
        total_pages = len(battle_log)

        if total_pages < 1:
            return await ctx.send(
                "You don't have any battles logged. Use the `-brawl` command to brawl!"
            )

        embeds = []

        for page_num, entry_json in enumerate(battle_log, start=1):
            entry: BattleLogEntry = await BattleLogEntry.from_json(entry_json, self.bot)

            embed = discord.Embed(
                color=LOG_COLORS[entry.result],
                timestamp=datetime.utcfromtimestamp(entry.timestamp)
            )
            embed.set_author(
                name=f"{ctx.author.name}'s Battle Log", icon_url=ctx.author.avatar_url
            )
            embed.description = (
                f"Opponent: **{entry.opponent}**"
                f"\nResult: **{entry.result}**"
                f"\nGame Mode: {gamemode_emotes[entry.game_mode]} **{entry.game_mode}**"
            )

            player_value = (
                f"Brawler: {brawler_emojis[entry.player_brawler_name]}"
                f" **{entry.player_brawler_name}**"
                f"\nBrawler Level: **{level_emotes['level_' + str(entry.player_brawler_level)]}**"
                f"\nBrawler Trophies: {emojis['trophies']} **{entry.player_brawler_trophies}**"
                f"\nReward Trophies: {emojis['trophies']} **{entry.player_reward_trophies}**"
            )
            embed.add_field(name="Your Stats", value=player_value)

            opponent_value = (
                f"Brawler: {brawler_emojis[entry.opponent_brawler_name]}"
                f" **{entry.opponent_brawler_name}**"
                f"\nBrawler Level: **{level_emotes['level_' + str(entry.opponent_brawler_level)]}**"
                f"\nBrawler Trophies: {emojis['trophies']} **{entry.opponent_brawler_trophies}**"
                f"\nReward Trophies: {emojis['trophies']} **{entry.opponent_reward_trophies}**"
            )
            embed.add_field(name="Opponent's Stats", value=opponent_value)

            embed.set_footer(text=f"Log {page_num} of {total_pages}")

            embeds.append(embed)

        await menu(ctx, embeds, DEFAULT_CONTROLS)

    @commands.command(name="gamemode")
    @maintenance()
    async def _gamemode(self, ctx: Context, *, gamemode: str):
        """Show info about a game mode"""

        try:
            gamemode = self.parse_gamemode(gamemode)
        except AmbiguityError as e:
            return await ctx.send(e)

        if gamemode is None:
            return await ctx.send("Unable to identify game mode.")

        if gamemode not in ["Gem Grab", "Solo Showdown", "Brawl Ball"]:
            return await ctx.send(
                "The game only supports **Gem Grab**, **Solo Showdown** and"
                " **Brawl Ball** at the moment. More game modes will be added soon!"
            )

        embed = discord.Embed(
            color=EMBED_COLOR,
            # title=f"{gamemode_emotes[gamemode]} {gamemode}",
            description=self.GAMEMODES[gamemode]["desc"]
        )
        embed.set_author(
            name=gamemode, icon_url=gamemode_thumb.format(gamemode.replace(" ", "-"))
        )

        await ctx.send(embed=embed)

    @commands.group(name="club")
    @commands.is_owner()
    @maintenance()
    async def _club(self, ctx: Context):
        """Show all club related commands"""

    @_club.command(name="create")
    @maintenance()
    async def _create_club(self, ctx: Context):
        """Create a club"""

        if await self.config.user(ctx.author).club() is not None:
            return await ctx.send("You are already in a club!")

        try:
            club: Club = await Club.create_club(self.config, ctx)
        except ValueError:
            return await ctx.send("Error! Input must be a valid number.")
        except asyncio.TimeoutError:
            return await ctx.send("Error! You took too long to respond.")
        except NameError:
            return await ctx.send("Error! Club type must be one of `open`, `closed`, or `invite`.")

        embeds = await club.show_club(club.to_json(), self.bot, self.config, self.get_league_data)

        await menu(ctx, embeds, DEFAULT_CONTROLS)

    @_club.command(name="my")
    @maintenance()
    async def _show_my_club(self, ctx: Context):
        """Show your club details, if in any club"""

        club = None
        club_id = await self.config.user(ctx.author).club()
        clubs = await self.config.clubs()
        for club_ in clubs:
            if club_["id"] == club_id:
                club = club_
                break

        if club is None:
            return await ctx.send("You are not in any club!")

        embeds = await Club.show_club(club, self.bot, self.config, self.get_league_data)

        try:
            await menu(ctx, embeds, DEFAULT_CONTROLS)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to send embeds."
                " Please give/ask someone to give me that permission."
            )

    @_club.command(name="leave")
    @maintenance()
    async def _leave_club(self, ctx: Context):
        """Leave your current club"""

        club_id = await self.config.user(ctx.author).club()
        if club_id is not None:
            msg = await ctx.send("Are you sure you want to leave your club?")
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            await ctx.bot.wait_for("reaction_add", check=pred)

            if pred.result is True:
                club = await Club.club_from_id(club_id, self.config, self.bot)
                await club.remove_user(ctx.author, self.config)
                await self.config.user(ctx.author).club.set(None)
                await ctx.send("Left the club!")
            else:
                await ctx.send("Cancelled leaving club.")
        else:
            await ctx.send("You are not in a club!")

    @_club.command(name="search")
    @maintenance()
    async def _search_club(self, ctx: Context, *, name: str):
        """Search for a club from it's name"""

        all_clubs = await self.config.clubs()

        # clubs = []
        total = 0
        clubs_txt = ""
        for club in all_clubs:
            if name.lower() in club["name"].lower():
                club = await Club.from_json(club, self.bot)
                if len(club.all_members) > 0:
                    clubs_txt += (
                        f"\n`{total+1:02d}.` {club_icons[f'club{club.icon_num}']} **{club.name}**"
                        f" (ID: `{club.id}`) - `{len(club.all_members)}/100` {emojis['friends']} |"
                        f" {emojis['trophies']} `{await club.total_trophies(self.config):,}`"
                    )
                    total += 1

        embed = discord.Embed(colour=EMBED_COLOR, description=f"{total} result(s) found.")

        if clubs_txt.strip():
            embed.add_field(name="\u200b\n", value=clubs_txt.strip())

        embed.set_author(name=f"Club Search - {name}")

        await ctx.send(embed=embed)

    @_club.command(name="join")
    @maintenance()
    async def _join_club(self, ctx: Context, *, club_id: str):
        """Join a club from it's ID"""

        if await self.config.user(ctx.author).club() is not None:
            return await ctx.send(
                "You are already in a club! You can leave it by using `club leave` command."
            )

        club = await Club.club_from_id(club_id.upper(), self.config, self.bot)

        if club is None:
            return await ctx.send(f"Club with ID `{club_id}` doesn't exist.")

        if len(club.all_members) == 100:
            return await ctx.send("The club is full!")

        try:
            await club.add_user(ctx.author, self.config)
        except ValueError as e:
            return await ctx.send(e)

        await self.config.user(ctx.author).club.set(club_id)
        await ctx.send("Joined the club!")

    @_club.command(name="info")
    @maintenance()
    async def _club_info(self, ctx: Context, *, club_id: str):
        """Display info about club with given ID"""

        club: Club = await Club.club_from_id(club_id.upper(), self.config, self.bot)
        if club is None:
            return await ctx.send(f"Club with ID `{club_id}` doesn't exist.")

        embeds = await club.show_club(club, self.bot, self.config, self.get_league_data)
        await menu(ctx, embeds, DEFAULT_CONTROLS)

    @_club.command(name="promote")
    @maintenance()
    async def _club_promote(self, ctx: Context, *, user: discord.User):
        """Promote specified user"""

        club_id = await self.config.user(ctx.author).club()
        club: Club = await Club.club_from_id(club_id, self.config, self.bot)

        if not (
            ctx.author.id == club.president.id
            or ctx.author in club.vice_presidents
        ):
            return await ctx.send(
                "You must be club's president or a vice-president to promote other members."
            )

        try:
            await club.promote_user(user, ctx, self.config)
        except ValueError as e:
            await ctx.send(e)
