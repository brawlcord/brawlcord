import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
from redbot.core import Config
from redbot.core.commands import Context
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_timedelta
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils.predicates import MessagePredicate

from .utils.battlelog import BattleLogEntry, PartialBattleLogEntry
from .utils.box import Box
from .utils.constants import default_stats, EMBED_COLOR
from .utils.emojis import (
    brawler_emojis, emojis, gamemode_emotes, league_emojis, rank_emojis, sp_icons
)
from .utils.errors import AmbiguityError
from .utils.shop import Shop

reward_types = {
    1: ["Gold", emojis["gold"]],
    3: ["Brawler", brawler_emojis],
    6: ["Brawl Box", emojis["brawlbox"]],
    7: ["Tickets", emojis['ticket']],
    9: ["Token Doubler", emojis['tokendoubler']],
    10: ["Mega Box", emojis["megabox"]],
    12: ["Power Points", emojis["powerpoint"]],
    13: ["Game Mode", gamemode_emotes],
    14: ["Big Box", emojis["bigbox"]]
}


class MixinMeta(ABC):
    """Mixin meta class for type hinting.

    It also defines all the helper functions.
    """

    def __init__(self, *_args):
        self.bot: Red
        self.config: Config

        self.BRAWLERS: dict
        self.REWARDS: dict
        self.XP_LEVELS: dict
        self.RANKS: dict
        self.TROPHY_ROAD: dict
        self.LEVEL_UPS: dict
        self.GAMEMODES: dict
        self.LEAGUES: dict

    @abstractmethod
    async def initialize(self):
        raise NotImplementedError

    async def get_player_stat(
        self, user: discord.User, stat: str,
        is_iter=False, substat: str = None
    ):
        """Get stats of a player."""

        if not is_iter:
            return await getattr(self.config.user(user), stat)()

        async with getattr(self.config.user(user), stat)() as stat:
            if not substat:
                return stat
            else:
                return stat[substat]

    async def update_player_stat(
        self, user: discord.User, stat: str, value,
        substat: str = None, sub_index=None, add_self=False
    ):
        """Update stats of a player."""

        if substat:
            async with getattr(self.config.user(user), stat)() as stat:
                if not sub_index:
                    if not add_self:
                        stat[substat] = value
                    else:
                        stat[substat] += value
                else:
                    if not add_self:
                        stat[substat][sub_index] = value
                    else:
                        stat[substat][sub_index] += value
        else:
            stat_attr = getattr(self.config.user(user), stat)
            if not add_self:
                old_val = 0
            else:
                old_val = await self.get_player_stat(user, stat)
            await stat_attr.set(value + old_val)

    async def get_trophies(
        self, user: discord.User,
        pb=False, brawler_name: str = None
    ):
        """Get total trophies or trophies of a specified Brawler of an user.

        Returns total trophies if a brawler is not specified.
        """

        brawlers = await self.get_player_stat(user, "brawlers")

        stat = "trophies" if not pb else "pb"

        if not brawler_name:
            return sum([brawlers[brawler][stat] for brawler in brawlers])
        else:
            return brawlers[brawler_name][stat]

    async def brawl_rewards(
        self,
        user: discord.User,
        points: int,
        gm: str,
        is_starplayer=False,
    ):
        """Adjust user variables and return embeds containing reward."""

        star_token = 0
        if points > 0:
            reward_tokens = 20
            reward_xp = 8
            position = 1
            async with self.config.user(user).todays_st() as todays_st:
                if gm not in todays_st:
                    star_token = 1
                    todays_st.append(gm)
        elif points < 0:
            reward_tokens = 10
            reward_xp = 4
            position = 2
        else:
            reward_tokens = 15
            reward_xp = 6
            position = 0

        if is_starplayer:
            reward_xp += 10

        tokens_in_bank = await self.get_player_stat(user, 'tokens_in_bank')

        if reward_tokens > tokens_in_bank:
            reward_tokens = tokens_in_bank

        tokens_in_bank -= reward_tokens

        # brawler trophies
        selected_brawler = await self.get_player_stat(
            user, 'selected', is_iter=True, substat='brawler')
        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True, substat=selected_brawler)
        trophies = brawler_data['trophies']

        reward_trophies = self.trophies_to_reward_mapping(trophies, '3v3', position)

        trophies += reward_trophies

        token_doubler = await self.get_player_stat(user, 'token_doubler')

        upd_td = token_doubler - reward_tokens
        if upd_td < 0:
            upd_td = 0

        if token_doubler > reward_tokens:
            reward_tokens *= 2
        else:
            reward_tokens += token_doubler

        await self.update_player_stat(
            user, 'tokens', reward_tokens, add_self=True)
        await self.update_player_stat(user, 'tokens_in_bank', tokens_in_bank)
        await self.update_player_stat(user, 'xp', reward_xp, add_self=True)
        await self.update_player_stat(
            user, 'brawlers', trophies,
            substat=selected_brawler, sub_index='trophies'
        )
        await self.update_player_stat(user, 'token_doubler', upd_td)
        await self.update_player_stat(
            user, 'startokens', star_token, add_self=True
        )
        await self.handle_pb(user, selected_brawler)

        user_avatar = user.avatar_url

        embed = discord.Embed(color=EMBED_COLOR, title="Rewards")
        embed.set_author(name=user.name, icon_url=user_avatar)

        reward_xp_str = (
            "{}".format(
                f'{reward_xp} (Star Player)' if is_starplayer
                else f'{reward_xp}'
            )
        )

        embed.add_field(name="Trophies",
                        value=f"{emojis['trophies']} {reward_trophies}")
        embed.add_field(
            name="Tokens", value=f"{emojis['token']} {reward_tokens}")
        embed.add_field(name="Experience",
                        value=f"{emojis['xp']} {reward_xp_str}")

        if token_doubler > 0:
            embed.add_field(
                name="Token Doubler",
                value=f"{emojis['tokendoubler']} x{upd_td} remaining!"
            )

        if star_token:
            embed.add_field(
                name="Star Token",
                value=f"{emojis['startoken']} 1",
                inline=False
            )

        rank_up = await self.handle_rank_ups(user, selected_brawler)
        trophy_road_reward = await self.handle_trophy_road(user)

        return (embed, trophies-reward_trophies, reward_trophies), rank_up, trophy_road_reward

    def trophies_to_reward_mapping(
        self, trophies: int, game_type="3v3", position=1
    ):

        # position correlates with the list index

        if trophies in range(0, 50):
            reward = self.REWARDS[game_type]["0-49"][position]
        elif trophies in range(50, 100):
            reward = self.REWARDS[game_type]["50-99"][position]
        elif trophies in range(100, 200):
            reward = self.REWARDS[game_type]["100-199"][position]
        elif trophies in range(200, 300):
            reward = self.REWARDS[game_type]["200-299"][position]
        elif trophies in range(300, 400):
            reward = self.REWARDS[game_type]["300-399"][position]
        elif trophies in range(400, 500):
            reward = self.REWARDS[game_type]["400-499"][position]
        elif trophies in range(500, 600):
            reward = self.REWARDS[game_type]["500-599"][position]
        elif trophies in range(600, 700):
            reward = self.REWARDS[game_type]["600-699"][position]
        elif trophies in range(700, 800):
            reward = self.REWARDS[game_type]["700-799"][position]
        elif trophies in range(800, 900):
            reward = self.REWARDS[game_type]["800-899"][position]
        elif trophies in range(900, 1000):
            reward = self.REWARDS[game_type]["900-999"][position]
        elif trophies in range(1000, 1100):
            reward = self.REWARDS[game_type]["1000-1099"][position]
        elif trophies in range(1100, 1200):
            reward = self.REWARDS[game_type]["1100-1199"][position]
        else:
            reward = self.REWARDS[game_type]["1200+"][position]

        return reward

    async def xp_handler(self, user: discord.User):
        """Handle xp level ups."""

        xp = await self.get_player_stat(user, 'xp')
        lvl = await self.get_player_stat(user, 'lvl')

        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        if xp >= next_xp:
            carry = xp - next_xp
        else:
            return False

        await self.update_player_stat(user, 'xp', carry)
        await self.update_player_stat(user, 'lvl', lvl + 1)

        level_up_msg = f"Level up! You have reached level {lvl+1}."

        reward_tokens = self.XP_LEVELS[str(lvl)]["TokensRewardCount"]

        tokens = await self.get_player_stat(user, 'tokens')

        token_doubler = await self.get_player_stat(user, 'token_doubler')

        upd_td = token_doubler - reward_tokens
        if upd_td < 0:
            upd_td = 0

        if token_doubler > reward_tokens:
            reward_tokens *= 2
        else:
            reward_tokens += token_doubler

        reward_msg = f"Rewards: {reward_tokens} {emojis['token']}"

        tokens += reward_tokens
        await self.update_player_stat(user, 'tokens', tokens)
        await self.update_player_stat(user, 'token_doubler', upd_td)

        return (level_up_msg, reward_msg)

    async def handle_pb(self, user: discord.User, brawler: str):
        """Handle personal best changes."""

        # individual brawler
        trophies = await self.get_trophies(user=user, brawler_name=brawler)
        pb = await self.get_trophies(user=user, pb=True, brawler_name=brawler)

        if trophies > pb:
            await self.update_player_stat(
                user, 'brawlers', trophies, substat=brawler, sub_index='pb')

    def get_rank(self, pb):
        """Return rank of the Brawler based on its personal best."""

        for rank in self.RANKS:
            start = self.RANKS[rank]["ProgressStart"]
            # 1 is not subtracted as we're calling range
            end = start + self.RANKS[rank]["Progress"]
            if pb in range(start, end):
                return int(rank)
        else:
            return 35

    async def handle_rank_ups(self, user: discord.User, brawler: str):
        """Function to handle Brawler rank ups.

        Returns an embed containing rewards if a brawler rank ups.
        """

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True, substat=brawler)

        pb = brawler_data['pb']
        rank = brawler_data['rank']

        rank_as_per_pb = self.get_rank(pb)

        if rank_as_per_pb <= rank:
            return False

        await self.update_player_stat(
            user, 'brawlers', rank_as_per_pb, brawler, 'rank')

        rank_up_tokens = self.RANKS[str(rank)]["PrimaryLvlUpRewardCount"]

        token_doubler = await self.get_player_stat(user, 'token_doubler')

        upd_td = token_doubler - rank_up_tokens
        if upd_td < 0:
            upd_td = 0

        if token_doubler > rank_up_tokens:
            rank_up_tokens *= 2
        else:
            rank_up_tokens += token_doubler

        rank_up_starpoints = self.RANKS[str(rank)]["SecondaryLvlUpRewardCount"]

        await self.update_player_stat(
            user, 'tokens', rank_up_tokens, add_self=True)
        await self.update_player_stat(
            user, 'starpoints', rank_up_starpoints, add_self=True)
        await self.update_player_stat(
            user, 'token_doubler', upd_td)

        embed = discord.Embed(
            color=EMBED_COLOR,
            title=f"Brawler Rank Up! {rank} → {rank_as_per_pb}"
        )
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(
            name="Brawler", value=f"{brawler_emojis[brawler]} {brawler}")
        embed.add_field(
            name="Tokens", value=f"{emojis['token']} {rank_up_tokens}")
        if rank_up_starpoints:
            embed.add_field(
                name="Star Points",
                value=f"{emojis['starpoints']} {rank_up_starpoints}"
            )
        if token_doubler > 0:
            embed.add_field(
                name="Token Doubler",
                value=f"{emojis['tokendoubler']} x{upd_td} remaining!",
                inline=False
            )
        return embed

    async def handle_trophy_road(self, user: discord.User):
        """Function to handle trophy road progress."""

        trophies = await self.get_trophies(user)
        tppased = await self.get_player_stat(user, 'tppassed')

        for tier in self.TROPHY_ROAD:
            if tier in tppased:
                continue
            threshold = self.TROPHY_ROAD[tier]['Trophies']

            if trophies > threshold:
                async with self.config.user(user).tppassed() as tppassed:
                    tppassed.append(tier)
                async with self.config.user(user).tpstored() as tpstored:
                    tpstored.append(tier)

                reward_name, reward_emoji, reward_str = self.tp_reward_strings(
                    self.TROPHY_ROAD[tier], tier)

                desc = "Claim the reward by using the `-rewards` command!"
                title = f"Trophy Road Reward [{threshold} trophies]"
                embed = discord.Embed(
                    color=EMBED_COLOR, title=title, description=desc)
                embed.set_author(name=user.name, icon_url=user.avatar_url)
                embed.add_field(name=reward_name,
                                value=f"{reward_emoji} {reward_str}")

                return embed

        else:
            return False

    def tp_reward_strings(self, reward_data, tier):
        reward_type = reward_data["RewardType"]
        reward_name = reward_types[reward_type][0]
        reward_emoji_root = reward_types[reward_type][1]
        if reward_type not in [3, 13]:
            reward_str = f"x{self.TROPHY_ROAD[tier]['RewardCount']}"
            reward_emoji = reward_emoji_root
        else:
            reward_str = self.TROPHY_ROAD[tier]['RewardExtraData']
            if reward_type == 3:
                reward_emoji = reward_emoji_root[reward_str]
            else:
                if reward_str == "Brawl Ball":
                    reward_emoji = reward_emoji_root[reward_str]
                elif reward_str == "Showdown":
                    reward_emoji = reward_emoji_root["Solo Showdown"]
                else:
                    reward_emoji = emojis["bsstar"]

        return reward_name, reward_emoji, reward_str

    async def handle_reward_claims(self, ctx: Context, reward_number: str):
        """Function to handle reward claims."""

        user = ctx.author

        reward_type = self.TROPHY_ROAD[reward_number]["RewardType"]
        reward_count = self.TROPHY_ROAD[reward_number]["RewardCount"]
        reward_extra = self.TROPHY_ROAD[reward_number]["RewardExtraData"]

        if reward_type == 1:
            await self.update_player_stat(
                user, 'gold', reward_count, add_self=True)

        elif reward_type == 3:
            async with self.config.user(user).brawlers() as brawlers:
                brawlers[reward_extra] = default_stats

        elif reward_type == 6:
            async with self.config.user(user).boxes() as boxes:
                boxes['brawl'] += reward_count

            brawler_data = await self.get_player_stat(
                user, 'brawlers', is_iter=True)

            box = Box(self.BRAWLERS, brawler_data)
            embed = await box.brawlbox(self.config.user(user), user)

            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                return await ctx.send(
                    "I do not have the permission to embed a link."
                    " Please give/ask someone to give me that permission."
                )

        elif reward_type == 7:
            await self.update_player_stat(
                user, 'tickets', reward_count, add_self=True)

        elif reward_type == 9:
            await self.update_player_stat(
                user, 'token_doubler', reward_count, add_self=True)

        elif reward_type == 10:
            async with self.config.user(user).boxes() as boxes:
                boxes['mega'] += reward_count

            brawler_data = await self.get_player_stat(
                user, 'brawlers', is_iter=True)

            box = Box(self.BRAWLERS, brawler_data)
            embed = await box.megabox(self.config.user(user), user)

            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                return await ctx.send(
                    "I do not have the permission to embed a link."
                    " Please give/ask someone to give me that permission."
                )

        elif reward_type == 12:
            await ctx.send("Enter the name of Brawler to add powerpoints to:")
            pred = await self.bot.wait_for(
                "message", check=MessagePredicate.same_context(ctx)
            )

            brawler = pred.content
            # for users who input 'el_primo'
            brawler = brawler.replace("_", " ")

            brawler = brawler.title()

            user_brawlers = await self.get_player_stat(
                user, 'brawlers', is_iter=True)

            if brawler not in user_brawlers:
                return await ctx.send(f"You do not own {brawler}!")

            total_powerpoints = (
                await self.get_player_stat(user, 'brawlers', is_iter=True, substat=brawler)
            )['total_powerpoints']

            if total_powerpoints == 1410:
                return await ctx.send(
                    f"{brawler} can not recieve more powerpoints."
                )
            elif total_powerpoints + reward_count > 1410:
                return await ctx.send(
                    f"{brawler} can not recieve {reward_count} powerpoints."
                )
            else:
                pass

            await self.update_player_stat(
                user, 'brawlers', reward_count, substat=brawler,
                sub_index='powerpoints', add_self=True
            )
            await self.update_player_stat(
                user, 'brawlers', reward_count, substat=brawler,
                sub_index='total_powerpoints', add_self=True
            )

            await ctx.send(f"Added {reward_count} powerpoints to {brawler}.")

        elif reward_type == 13:
            async with self.config.user(user).gamemodes() as gamemodes:
                if reward_extra == "Brawl Ball":
                    gamemodes.append(reward_extra)

                elif reward_extra == "Showdown":
                    gamemodes.append("Solo Showdown")
                    gamemodes.append("Duo Showdown")

                elif reward_extra == "Ticket Events":
                    gamemodes.append("Robo Rumble")
                    gamemodes.append("Boss Fight")
                    gamemodes.append("Big Game")

                elif reward_extra == "Team Events":
                    gamemodes.append("Heist")
                    gamemodes.append("Bounty")
                    gamemodes.append("Siege")

                elif reward_extra == "Solo Events":
                    gamemodes.append("Lone Star")
                    gamemodes.append("Takedown")

        elif reward_type == 14:
            async with self.config.user(user).boxes() as boxes:
                boxes['big'] += reward_count

            brawler_data = await self.get_player_stat(
                user, 'brawlers', is_iter=True)

            box = Box(self.BRAWLERS, brawler_data)
            embed = await box.bigbox(self.config.user(user), user)

            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                return await ctx.send(
                    "I do not have the permission to embed a link."
                    " Please give/ask someone to give me that permission."
                )

        async with self.config.user(user).tpstored() as tpstored:
            tpstored.remove(reward_number)

    def get_sp_info(self, brawler_name: str, sp: str):
        """Return name and emoji of the Star Power."""

        for brawler in self.BRAWLERS:
            if brawler == brawler_name:
                sp_name = self.BRAWLERS[brawler][sp]['name']
                sp_ind = int(sp[2]) - 1
                sp_icon = sp_icons[brawler][sp_ind]

        return sp_name, sp_icon

    def parse_brawler_name(self, brawler_name: str):
        """Parse brawler name."""
        # for users who input 'el_primo'
        brawler_name = brawler_name.replace("_", " ")

        brawler_name = brawler_name.title()

        if brawler_name not in self.BRAWLERS:
            return False

        return brawler_name

    async def leaderboard_handler(
        self, ctx: Context, title: str, thumb_url: str,
        padding: int, pb=False, brawler_name=None
    ):
        """Handler for all leaderboards."""

        all_users = await self.config.all_users()
        users = []
        for user_id in all_users:
            try:
                user = self.bot.get_user(user_id)
                if not user:
                    continue
                trophies = await self.get_trophies(
                    user, pb=pb, brawler_name=brawler_name)
                users.append((user, trophies))
            except Exception:
                pass

        # remove duplicates
        users = list(set(users))
        users = sorted(users, key=lambda k: k[1], reverse=True)

        embed_desc = (
            "Check out who is at the top of the Brawlcord leaderboard!\n\u200b"
        )
        add_user = True
        # return first 10 (or fewer) members
        for i in range(10):
            try:
                trophies = users[i][1]
                user = users[i][0]
                if brawler_name:
                    emoji = await self.get_rank_emoji(user, brawler_name)
                else:
                    _, emoji = await self.get_league_data(trophies)
                if user.id == ctx.author.id:
                    embed_desc += (
                        f"**\n`{(i+1):02d}.` {user} {emoji}"
                        f"{trophies:>{padding},}**"
                    )
                    add_user = False
                else:
                    embed_desc += (
                        f"\n`{(i+1):02d}.` {user} {emoji}"
                        f"{trophies:>{padding},}"
                    )
            except Exception:
                pass

        embed = discord.Embed(color=EMBED_COLOR, description=embed_desc)
        embed.set_author(name=title, icon_url=ctx.me.avatar_url)
        embed.set_thumbnail(url=thumb_url)

        # add rank of user
        if add_user:
            for idx, user in enumerate(users):
                if ctx.author == user[0]:
                    val_str = ""
                    try:
                        trophies = users[idx][1]
                        user = users[idx][0]
                        if brawler_name:
                            emoji = await self.get_rank_emoji(
                                user, brawler_name)
                        else:
                            _, emoji = await self.get_league_data(trophies)
                        val_str += (
                            f"\n**`{(idx+1):02d}.` {user} {emoji}"
                            f"{trophies:>{padding},}**"
                        )
                    except Exception:
                        pass
            try:
                embed.add_field(name="Your position", value=val_str)
            except UnboundLocalError:
                # happens only in case of brawlers
                embed.add_field(name=f"\u200bNo one owns {brawler_name}!",
                                value="Open boxes to unlock new Brawlers.")
            except Exception:
                pass

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    async def get_league_data(self, trophies: int):
        """Return league number and emoji."""
        for league in self.LEAGUES:
            name = self.LEAGUES[league]["League"]
            start = self.LEAGUES[league]["ProgressStart"]
            end = start + self.LEAGUES[league]["Progress"]

            # end = 14000 for Star V
            if end != 14000:
                if trophies in range(start, end + 1):
                    break
            else:
                if trophies >= 14000:
                    name = "Star V"

        if name == "No League":
            return False, league_emojis[name]

        league_name = name.split(" ")[0]
        league_number = name.split(" ")[1]

        return league_number, league_emojis[league_name]

    async def get_rank_emoji(self, user: discord.User, brawler: str):

        data = await self.get_player_stat(
            user, 'brawlers', is_iter=True, substat=brawler)
        rank = self.get_rank(data['pb'])

        return rank_emojis['br' + str(rank)]

    def _box_name(self, box: str):
        """Return box name"""

        return box.split("box")[0].title() + " Box"

    async def create_shop(self, user: discord.User, update=True) -> Shop:

        brawler_data = await self.get_player_stat(
            user, 'brawlers', is_iter=True
        )

        shop = Shop(self.BRAWLERS, brawler_data)
        shop.generate_shop_items()
        data = shop.to_json()

        await self.config.user(user).shop.set(data)

        if update:
            time_now = datetime.utcnow()
            epoch = datetime(1970, 1, 1)
            # get timestamp in UTC
            timestamp = (time_now - epoch).total_seconds()
            await self.config.shop_reset_ts.set(timestamp)

        return shop

    async def _view_shop(self, ctx: Context):
        """Sends shop embeds."""

        user = ctx.author

        shop_data = await self.config.user(user).shop()
        if not shop_data:
            shop = await self.create_shop(user, update=False)
        else:
            shop = Shop.from_json(shop_data)

        last_reset = datetime.utcfromtimestamp(
            await self.config.shop_reset_ts()
        )

        next_reset = last_reset + timedelta(days=1)

        next_reset_str = humanize_timedelta(
            timedelta=next_reset - datetime.utcnow()
        )

        em = shop.create_items_embeds(user, next_reset_str)

        await menu(ctx, em, DEFAULT_CONTROLS)

    async def reset_st(self, user: discord.User):
        """Reset user star tokens list and update timestamp."""

        async with self.config.user(user).todays_st() as todays_st:
            todays_st.clear()

        time_now = datetime.utcnow()
        epoch = datetime(1970, 1, 1)
        # get timestamp in UTC
        timestamp = (time_now - epoch).total_seconds()
        await self.config.st_reset_ts.set(timestamp)

    async def save_battle_log(self, log_data: dict):
        """Save complete log entry."""

        if len(log_data) == 1:
            # One user is the bot.
            user = log_data[0]["user"]
            partial_logs = await self.config.user(user).partial_battle_log()
            partial_log_json = partial_logs[-1]

            partial_log = await PartialBattleLogEntry.from_json(partial_log_json, self.bot)
            player_extras = {
                "brawler_trophies": log_data[0]["trophies"],
                "reward_trophies": log_data[0]["reward"]
            }
            opponent_extras = {
                "brawler_trophies": log_data[0]["trophies"] + random.randint(-20, 20),
                "reward_trophies": 0
            }
            log_entry = BattleLogEntry(partial_log, player_extras, opponent_extras).to_json()
            async with self.config.user(user).battle_log() as battle_log:
                battle_log.append(log_entry)
        else:
            for i in [0, 1]:
                if i == 0:
                    other = 1
                else:
                    other = 0

                user = log_data[i]["user"]
                partial_logs = await self.config.user(user).partial_battle_log()
                partial_log_json = partial_logs[-1]

                partial_log = await PartialBattleLogEntry.from_json(partial_log_json, self.bot)
                player_extras = {
                    "brawler_trophies": log_data[i]["trophies"],
                    "reward_trophies": log_data[i]["reward"]
                }
                opponent_extras = {
                    "brawler_trophies": log_data[other]["trophies"],
                    "reward_trophies": log_data[other]["reward"]
                }
                log_entry = BattleLogEntry(partial_log, player_extras, opponent_extras).to_json()
                async with self.config.user(user).battle_log() as battle_log:
                    battle_log.append(log_entry)

    def parse_gamemode(self, gamemode: str):
        """Returns full game mode name from user input.

        Returns `None` if no game mode is found.

        Raises
        --------
        AmbiguityError
            If `gamemode.lower()` is "showdown"
        """

        gamemode = gamemode.strip()

        # for users who input 'gem-grab' or 'gem_grab'
        gamemode = gamemode.replace("-", " ")
        gamemode = gamemode.replace("_", " ")

        if gamemode.lower() == "showdown":
            raise AmbiguityError("Please select one between Solo and Duo Showdown.")

        possible_names = {
            "Gem Grab": ["gem grab", "gemgrab", "gg", "gem"],
            "Brawl Ball": ["brawl ball", "brawlball", "bb", "bball", "ball"],
            "Solo Showdown": [
                "solo showdown", "ssd", "solo sd",
                "soloshowdown", "solo", "s sd"
            ],
            "Duo Showdown": [
                "duo showdown", "dsd", "duo sd", "duoshowdown", "duo", "d sd"
            ],
            "Bounty": ["bounty", "bonty", "bunty"],
            "Heist": ["heist", "heis"],
            "Lone Star": ["lone star", "lonestar", "ls", "lone"],
            "Takedown": ["takedown", "take down", "td"],
            "Robo Rumble": [
                "robo rumble", "rr", "roborumble", "robo", "rumble"
            ],
            "Big Game": ["big game", "biggame", "bg", "big"],
            "Boss Fight": ["boss fight", "bossfight", "bf", "boss"]
        }

        for gmtype in possible_names:
            modes = possible_names[gmtype]
            if gamemode.lower() in modes:
                return gmtype
        else:
            return None
