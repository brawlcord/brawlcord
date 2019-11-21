# Standard Library
import asyncio
import json
import logging
import random

from datetime import datetime, timedelta
from math import ceil
from typing import Optional

# Discord
import discord

# Redbot
from redbot.core import Config, commands, checks
from redbot.core.commands.context import Context
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu, start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate, MessagePredicate

from .brawlers import emojis, brawler_emojis, rank_emojis, Brawler, Shelly, Nita, Colt
from .utils import Box, default_stats


BaseCog = getattr(commands, "Cog", object)

log = logging.getLogger("red.brawlcord")

__version__ = "1.0.0"
__author__ = "Snowsee"

default_user = {
    "xp": 0,
    "gold": 0,
    "lvl": 1,
    "gems": 0,
    "starpoints": 0,
    "startokens": 0,
    "tickets": 0,
    "tokens": 0,
    "tokens_in_bank": 200,
    "token_doubler": 0,
    # "trophies": 0,
    "tutorial_finished": False,
    "bank_update_ts": None,
    "brawlers": {
        "Shelly": default_stats
    },
    "gamemodes": [
        "Gem Grab"
    ],
    "selected": {
        "brawler": "Shelly",
        "brawler_skin": "Default",
        "gamemode": "Gem Grab",
        "starpower": None
    },
    "tppassed": [],
    "tpstored": [],
    "brawl_stats": {
        "solo": [0, 0], # [wins, losses]
        "3v3_wins": [0, 0], # [wins, losses]
        "duo_wins": [0, 0], # [wins, losses]
    },
    "boxes": {
        "brawl": 0,
        "big": 0,
        "mega": 0
    }
}

brawlers_map = {
    "Shelly": Shelly,
    "Nita": Nita,
    "Colt": Colt
}

# tutorial_trophies = 10

imgur_links = {
    "shelly_tut": "https://i.imgur.com/QfKYzso.png"
}

gamemode_emotes = {
    "Big Game": "<:big_game:645925169344282624>",
    "Bounty": "<:bounty:645925169252270081>",
    "Boss Fight": "<:bossfight:645925170397052929>",
    "Brawl Ball": "<:brawlball:645925169650466816>",
    "Gem Grab": "<:gemgrab:645925169730289664>",
    "Duo Showdown": "<:duo_showdown:645925169805656076>",
    "Heist": "<:heist:645925170195988491>",
    "raid": "<:raid:645925170397052929>",
    "Siege": "<:siege:645925170481201163>",
    "Solo Showdown": "<:solo_showdown:645925170539921428>",
    "Robo Rumble": "<:roborumble:645925170594316288>",
    "Lone Star": "<:lonestar:645925170610962452>",
    "Takedown": "<:takedown:645925171034587146>",
}

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

spawn_text = {
    "Nita": "Bear",
    "Penny": "Cannon",
    "Jessie": "Turrent",
    "Pam": "Healing Station",
    "8-Bit": "Turret"
}

class Brawlcord(BaseCog, name="Brawlcord"):
    """Simulate Brawl Stars."""

    def __init__(self, bot):
        self.bot = bot

        # self._brawl_countdown = {}
        self.sessions = {}
        self.tasks = {}
        self.locks = {}

        self.config = Config.get_conf(self, 1_070_701_001, force_registration=True)

        self.path = bundled_data_path(self)

        self.config.register_user(**default_user)

        self.BRAWLERS: dict = None
        self.REWARDS: dict = None
        self.XP_LEVELS: dict = None
        self.RANKS: dict = None
        self.TROPHY_ROAD: dict = None

        def error_callback(fut):
            try:
                fut.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logging.exception("Error in something", exc_info=exc)
                print("Error in something:", exc)

        self.bank_update_task = self.bot.loop.create_task(self.update_token_bank())
        self.bank_update_task.add_done_callback(error_callback)

    async def initialize(self):
        brawlers_fp = bundled_data_path(self) / "brawlers.json"
        rewards_fp = bundled_data_path(self) / "rewards.json"
        xp_levels_fp = bundled_data_path(self) / "xp_levels.json"
        ranks_fp = bundled_data_path(self) / "ranks.json"
        trophy_road_fp = bundled_data_path(self) / "trophy_road.json"

        with brawlers_fp.open("r") as f:
            self.BRAWLERS = json.load(f)
        with rewards_fp.open("r") as f:
            self.REWARDS = json.load(f)
        with xp_levels_fp.open("r") as f:
            self.XP_LEVELS = json.load(f)
        with ranks_fp.open("r") as f:
            self.RANKS = json.load(f)
        with trophy_road_fp.open("r") as f:
            self.TROPHY_ROAD = json.load(f)

    # @commands.command(name="brawl", aliases=["b"])
    # @commands.guild_only()
    # # @commands.cooldown(rate=1, per=60, type=commands.BucketType.guild)
    async def brawl(
        self,
        ctx: Context,
        teammate1: discord.Member = None,
        teammate2: discord.Member = None
    ):
        """Brawl against others!"""

        # author = ctx.author
        # guild = ctx.guild

        # tutorial_finished = await self.get_player_stat(author, "tutorial_finished")

        # if not tutorial_finished:
        #     return await ctx.send(f"{author.mention} You have not finished tutorial yet."
        #                           "Use  `-tutorial` to start tutorial.")

        # teammates = [teammate1, teammate2]

        # players = [author]

        # for teammate in teammates:
        #     if teammate:
        #         if teammate == author:
        #             return await ctx.send("You can't play with yourself!")
        #         elif teammate == guild.me:
        #             return await ctx.send("I can't play!")
        #         players.append(teammate)

        # # await ctx.send(teammates)

        # results = {}

        # for player in players:
        #     selected_brawler = (await self.get_player_stat(player, "selected"))["brawler"]

        #     user_brawler_level = (await self.get_player_stat(player, "brawlers"))[selected_brawler]["level"]

        #     opp_brawler, opp_brawler_level, opp_brawler_sp = self.matchmaking(
        #         user_brawler_level)

        #     user1: Brawler = brawlers_map[selected_brawler](
        #         self.BRAWLERS, selected_brawler)
        #     # opp1: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)
        #     opp1 = Shelly(self.BRAWLERS, "Shelly")

        #     # await ctx.send(embed=user1.brawler_info("Shelly", 10, 10, 5, 0, 200))

        #     user_health = user1._health(user_brawler_level)
        #     opp_health = opp1._health(opp_brawler_level)

        #     opp_health -= user1._attack(user_brawler_level)

        #     user_counter = 0
        #     opp_counter = 0

        #     winner = "Computer"
        #     margin = 0

        #     while True:
        #         # print(f"You before attack: {user_health}")
        #         # print(f"Computer before attack: {opp_health}")
        #         if user_counter > 0 and user_counter % 5 == 0:
        #             res = user1._ult(user_brawler_level)
        #             opp_health -= res
        #             if res > 0:
        #                 user_counter += 1
        #         if opp_counter > 0 and opp_counter % 5 == 0:
        #             res = opp1._ult(opp_brawler_level)
        #             user_health -= res
        #             if res > 0:
        #                 opp_counter += 1

        #         else:
        #             res_u = user1._attack(user_brawler_level)
        #             res_o = opp1._attack(opp_brawler_level)

        #             if res_u > 0:
        #                 user_counter += 1
        #             if res_o > 0:
        #                 opp_counter += 1

        #             user_health -= res_o
        #             opp_health -= res_u

        #         # print(f"You after attack: {user_health}")
        #         # print(f"Computer after attack: {opp_health}")

        #         margin = abs(user_health-opp_health)

        #         if user_health <= 0 and opp_health > 0:
        #             break
        #         if opp_health <= 0 and user_health > 0:
        #             winner = "User"
        #             break
        #         if opp_health <= 0 and user_health <= 0:
        #             winner = "Draw"
        #             break
        #         else:
        #             continue

        #     if winner == "Computer":
        #         results[player] = {
        #             "brawl_res": -1,
        #             "margin": margin
        #         }
        #     elif winner == "User":
        #         results[player] = {
        #             "brawl_res": 1,
        #             "margin": margin
        #         }
        #     else:
        #         results[player] = {
        #             "brawl_res": 0,
        #             "margin": margin
        #         }

        # points = 0
        # for result in results:
        #     if results[result]['brawl_res'] == 1:
        #         points += 1
        #     elif results[result]['brawl_res'] == -1:
        #         points -= 1
        #     else:
        #         points += 0

        # starplayer = guild.me

        # player_mentions = ' '.join([player.mention for player in players])
        
        # if points > 0:
        #     # max_margin = 0
        #     # for result in results.keys():
        #     #     if results[result]['margin'] > max_margin:
        #     #         max_margin = results[result]['margin']
        #     #         starplayer = result
        #     #         if len(results) > 3:
        #     starplayer = random.choice([result for result in results])
        #     await ctx.send(f"{player_mentions} You won! Star Player: {starplayer}.")
        # elif points < 1:
        #     await ctx.send(f"{player_mentions} You lost! Star Player: {starplayer}.")
        # else:
        #     chance = random.randint(1, 2)
        #     if chance == 1:
        #         starplayer = random.choice([result for result in results])
        #     await ctx.send(f"The match ended in a draw! Star Player: {starplayer}.")

        # count = 0
        # for user in results:
        #     if user == starplayer:
        #         is_starplayer = True
        #     else:
        #         is_starplayer = False
        #     brawl_rewards, rank_up_rewards, trophy_road_reward = await self.brawl_rewards(user, points, is_starplayer)
            
        #     count += 1
        #     if count == 1:
        #         await ctx.send("Direct messaging rewards!")
        #     level_up = await self.xp_handler(user)
        #     try:
        #         await user.send(embed=brawl_rewards)
        #         if level_up:
        #             await user.send(f"{level_up[0]}\n{level_up[1]}")
        #         if rank_up_rewards:
        #             await user.send(embed=rank_up_rewards)
        #         if trophy_road_reward:
        #             await user.send(embed=trophy_road_reward)
        #     except:
        #         await ctx.send(f"Cannot direct message {user.mention}")
        #         await ctx.send(embed=brawl_rewards)
        #         if level_up:
        #             await ctx.send(f"{user.mention} {level_up[0]}\n{level_up[1]}")
        #             await ctx.send()
        #         if rank_up_rewards:
        #             await ctx.send(embed=rank_up_rewards)
        #         if trophy_road_reward:
        #             await ctx.send(embed=trophy_road_reward)

        pass

    @commands.command(name="brawl", aliases=["b"])
    @commands.guild_only()
    async def _brawl(self, ctx: Context, opponent: discord.User = None):
        """Brawl against others!"""

        guild = ctx.guild
        user = ctx.author

        user_brawler = await self.get_player_stat(user, "selected", is_iter=True, substat="brawler")
        brawler_data = await self.get_player_stat(user, "brawlers", is_iter=True, substat=user_brawler)
        user_brawler_level = brawler_data['level']

        gamemode = await self.get_player_stat(user, "selected", is_iter=True, substat="gamemode")

        ub: Brawler = brawlers_map[user_brawler](self.BRAWLERS, user_brawler)

        if opponent:
            opp_brawler = await self.get_player_stat(opponent, "selected", is_iter=True, substat="brawler")
            opp_data = await self.get_player_stat(opponent, "brawlers", is_iter=True, substat=opp_brawler)
            opp_brawler_level = brawler_data['level']

            # ob: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)

        else:
            opponent = guild.me
            opp_brawler, opp_brawler_level, opp_brawler_sp = self.matchmaking(user_brawler_level)

        ob: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)
        
        if opponent != guild.me:
            try:
                msg = await opponent.send(f"{user.mention} has challenged you for a brawl."
                    f" Game Mode: **{gamemode}**. Accept?")
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

                pred = ReactionPredicate.yes_or_no(msg, opponent)
                await ctx.bot.wait_for("reaction_add", check=pred)
                if pred.result is True:
                    # User responded with tick
                    pass
                else:
                    # User responded with cross
                    return await ctx.send(f"{user.mention} {opponent.mention} Brawl cancelled."
                    f" Reason: {opponent.name} rejected the challenge.")    
            except:
                return await ctx.send(f"{user.mention} {opponent.mention} Brawl cancelled." 
                    f" Reason: Unable to DM {opponent.name}. DMs are required to brawl!")
            
        first_move_chance = random.randint(1, 2)

        if first_move_chance == 1:
            first = ub
            second = ob
            first_player = user
            second_player = opponent
            first_brawler = user_brawler
            second_brawler = opp_brawler
            fp_brawler_level = user_brawler_level
            sp_brawler_level = opp_brawler_level
        else:
            first = ob
            second = ub
            first_player = opponent
            second_player = user
            first_brawler = opp_brawler
            second_brawler = user_brawler
            sp_brawler_level = user_brawler_level
            fp_brawler_level = opp_brawler_level
        
        winner, loser = await self.gemgrab(ctx, first, second, first_player, second_player, 
                            first_brawler, second_brawler, fp_brawler_level, sp_brawler_level)
        
        players = [first_player, second_player]
        
        starplayer = random.choice(players)

        if winner:
            # starplayer = winner
            await ctx.send(f"{first_player.mention} {second_player.mention} Match ended. Winner: {winner.name}!")
        else:
            # starplayer = random.choice(players)
            await ctx.send(f"{first_player.mention} {second_player.mention} The match ended in a draw!")
        
        starplayer = None

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

            if player == starplayer:
                is_starplayer = True
            else:
                is_starplayer = False
            brawl_rewards, rank_up_rewards, trophy_road_reward = await self.brawl_rewards(player, points, is_starplayer)
            
            count += 1
            if count == 1:
                await ctx.send("Direct messaging rewards!")
            level_up = await self.xp_handler(player)
            await player.send(embed=brawl_rewards)
            if level_up:
                await player.send(f"{level_up[0]}\n{level_up[1]}")
            if rank_up_rewards:
                await player.send(embed=rank_up_rewards)
            if trophy_road_reward:
                await player.send(embed=trophy_road_reward)

    @commands.command(name="tutorial", aliases=["tut"])
    @commands.guild_only()
    # @commands.cooldown(rate=1, per=60, type=commands.BucketType.guild)
    async def _tutorial(self, ctx: Context):
        """Begin the tutorial."""

        author = ctx.author
        guild = ctx.guild
        author_avatar = author.avatar_url

        finished_tutorial = await self.get_player_stat(author, "tutorial_finished")

        # if finished_tutorial:
        #     return await ctx.send(
        #         "You have already finished the tutorial."
        #         " It's time to test your skills in the real world!"
        #     )

        desc = ("Hi, I'm Shelly! I'll introduce you to the world of Brawlcord."
                " Don't worry Brawler, it will only take a minute!")

        embed = discord.Embed(
            colour=0x9D4D4F, title="Tutorial", description=desc)
        # embed.set_author(name=author, icon_url=author_avatar)
        embed.set_thumbnail(url=imgur_links["shelly_tut"])

        useful_commands = (
            "`-brawl [teammate-1] [teammate-2]` Sends you on a Brawl!"
            "\n`-tutorial` Begins the tutorial!"
        )

        embed.add_field(name="Useful Commands", value=useful_commands)

        await ctx.send(embed=embed)

        await self.update_player_stat(author, 'tutorial_finished', True)
        dt_now = datetime.utcnow()

        epoch = datetime(1970, 1, 1)

        # get timestamp in UTC 
        timestamp = (dt_now - epoch).total_seconds()

        await self.update_player_stat(author, 'bank_update_ts', timestamp)

    @commands.command(name="profile", aliases=["p", "pro"])
    async def _profile(self, ctx: Context, user: discord.User = None):
        """Display your or specified user's profile."""

        if not user:
            user = ctx.author
        
        embed = discord.Embed(colour=0xFFFFFF)
        embed.set_author(name=f"{user.name}'s Profile", icon_url=user.avatar_url)

        trophies = await self.get_trophies(user)
        embed.add_field(name="Trophies", value=f"{emojis['trophies']} {trophies:,}")

        pb = await self.get_trophies(user=user, pb=True)
        embed.add_field(name="Personal Best", value=f"{emojis['pb']} {pb:,}")

        xp = await self.get_player_stat(user, 'xp')
        lvl = await self.get_player_stat(user, 'lvl')
        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        embed.add_field(name="Experience Level", value=f"{emojis['xp']} {lvl} `{xp}/{next_xp}`")

        gold = await self.get_player_stat(user, 'gold')
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}")

        tokens = await self.get_player_stat(user, 'tokens')
        embed.add_field(name="Tokens", value=f"{emojis['token']} {tokens}")

        starpoints = await self.get_player_stat(user, 'starpoints')
        embed.add_field(name="Star Points", value=f"{emojis['starpoints']} {starpoints}")

        selected = await self.get_player_stat(user, 'selected', is_iter=True)
        brawler = selected['brawler']
        skin = selected['brawler_skin']
        gamemode = selected['gamemode']

        embed.add_field(name="Brawler", 
                value=f"{brawler_emojis[brawler]} {skin if skin != 'Default' else ''} {brawler}")
        embed.add_field(name="Game Mode", value=f"{gamemode_emotes[gamemode]} {gamemode}")

        await ctx.send(embed=embed)
    
    @commands.command(name="brawler", aliases=['binfo'])
    async def _brawler(self, ctx: Context, brawler_name: str, user: discord.User = None):
        """Get stats of a Brawler."""

        if not user:
            user = ctx.author
        
        brawlers = self.BRAWLERS

        # for users who input 'el_primo'
        brawler_name = brawler_name.replace("_", " ")

        brawler_name = brawler_name.title()

        for brawler in brawlers:
            if brawler_name in brawler:
                break
            else:
                brawler = None
        
        if not brawler:
            return await ctx.send(f"{brawler_name} does not exist.")
        
        owned_brawlers = await self.get_player_stat(user, 'brawlers', is_iter=True)

        owned = True if brawler in owned_brawlers else False

        b: Brawler = brawlers_map[brawler](self.BRAWLERS, brawler)

        if owned:
            brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True, substat=brawler)
            pp = brawler_data['powerpoints']
            next_level_pp = 20
            trophies = brawler_data['trophies']
            rank = brawler_data['rank']
            level = brawler_data['level']
            pb = brawler_data['pb']
            sp1 = brawler_data['sp1']
            sp2 = brawler_data['sp2']

            embed = b.brawler_info(brawler, trophies, pb, rank, level, pp, next_level_pp, sp1, sp2)

        else:
            embed = b.brawler_info(brawler)

        await ctx.send(embed=embed)
 
    @commands.group(name="rewards", autohelp=False)
    async def _rewards(self, ctx: Context):
        """View and claim collected trophy road rewards!"""
        pass            
    
    @_rewards.command(name="list")
    async def rewards_list(self, ctx: Context):
        """View collected trophy road rewards."""

        user = ctx.author
        
        tpstored = await self.get_player_stat(user, 'tpstored')

        desc = "Use `-rewards claim <reward_number>` or `-rewards claimall` to claim rewards!"
        embed = discord.Embed(color=0xFFA232, title="Rewards List", description=desc)
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        
        embed_str = ""
        
        for tier in tpstored:
            reward_data = self.TROPHY_ROAD[tier]
            reward_name, reward_emoji, reward_str = self.tp_reward_strings(reward_data, tier)

            embed_str += f"\n**{tier}.** {reward_name}: {reward_emoji} {reward_str}"
        
        embed.add_field(name="Rewards", value=embed_str.strip())

        await ctx.send(embed=embed)

    @_rewards.command(name="claim")
    async def rewards_claim(self, ctx: Context, reward_number: str):
        """Claim collected trophy road reward."""

        user = ctx.author
        
        tpstored = await self.get_player_stat(user, 'tpstored')

        if reward_number not in tpstored:
            return await ctx.send(f"You do not have {reward_number} collected.")
        
        await self.handle_reward_claims(ctx, reward_number)
        
        await ctx.send("Reward successfully claimed.")    
        
    @_rewards.command(name="claimall")
    async def rewards_claim_all(self, ctx: Context):
        user = ctx.author

        tpstored = await self.get_player_stat(user, 'tpstored')

        for tier in tpstored:
            await self.handle_reward_claims(ctx, tier)
        
        await ctx.send("Rewards successfully claimed.")    
    
    @commands.group(name="select", autohelp=False)
    async def _select(self, ctx: Context):
        """Select Brawler or game mode!"""
        pass
    
    @_select.command(name="brawler", aliases=['b'])
    async def select_brawler(self, ctx: Context, *, brawler_name: str):
        """Select Brawler to brawl with!"""

        user_owned = await self.get_player_stat(ctx.author, 'brawlers', is_iter=True)

        # for users who input 'el_primo'
        brawler_name = brawler_name.replace("_", " ")

        brawler_name = brawler_name.title()

        if brawler_name not in user_owned:
            return await ctx.send(f"You do not own {brawler_name}!")
        
        await self.update_player_stat(ctx.author, 'selected', brawler_name, substat='brawler')

        await ctx.send(f"Changed selected Brawler to {brawler_name}!")

    @_select.command(name="gamemode", aliases=['gm'])
    async def select_gamemode(self, ctx: Context, *, gamemode: str):
        """Select a game mode to brawl!"""

        return await ctx.send("The game only supports **Gem Grab** at the moment." 
                " More game modes will be added soon!")
        
        # for users who input 'gem-grab' or 'gem_grab'
        gamemode = gamemode.replace("-", " ")
        gamemode = gamemode.replace("_", " ")
        
        if gamemode.lower() == "showdown":
            return await ctx.send("Please select one between Solo and Duo Showdown.")
        
        possible_names = {
            "Gem Grab": ["gem grab", "gemgrab", "gg", "gem"],
            "Brawl Ball": ["brawl ball", "brawlball", "bb", "bball", "ball"],
            "Solo Showdown": ["solo showdown","ssd", "solo sd", "soloshowdown", "solo", "s sd"],
            "Duo Showdown": ["duo showdown", "dsd", "duo sd", "duoshowdown", "duo", "d sd"],
            "Bounty": ["bounty", "bonty", "bunty"],
            "Heist": ["heist", "heis"],
            "Lone Star": ["lone star", "lonestar", "ls", "lone"],
            "Takedown": ["takedown", "take down", "td"],
            "Robo Rumble": ["robo rumble", "rr", "roborumble", "robo", "rumble"],
            "Big Game": ["big game", "biggame", "bg", "big"],
            "Boss Fight": ["boss fight", "bossfight", "bf", "boss"]
        }
        
        for gmtype in possible_names:
            modes = possible_names[gmtype]
            if gamemode.lower() in modes:
                gamemode = gmtype
                break
        else:
            return await ctx.send("Unable to identify game mode.")

        user_owned = await self.get_player_stat(ctx.author, 'gamemodes', is_iter=True)
        
        if gamemode not in user_owned:
            return await ctx.send(f"You do not own {gamemode}!")
        
        await self.update_player_stat(ctx.author, 'selected', gamemode, substat='gamemode')

        await ctx.send(f"Changed selected game mode to {gamemode}!")
    
    @commands.command(name="emojis")
    @checks.is_owner()
    async def get_all_emotes(self, ctx: Context):
        """Get all emojis of the server."""

        guild = ctx.guild

        server_emojis = await guild.fetch_emojis()

        print("_emojis = {")
        for emoji in server_emojis:
            print(f"    \"{emoji.name}\": \"<:{emoji.name}:{emoji.id}>\",")
        print("}")
    
    @commands.command(name="box")
    async def open_brawl_box(self, ctx: Context):
        """Open a Brawl Box!"""
        user = ctx.author
        
        tokens = await self.get_player_stat(user, 'tokens')

        if tokens < 100:
            return await ctx.send("You do not have enough Tokens to open a brawl box.")
        
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        embed = await box.brawlbox(self.config.user(user), user)

        await ctx.send(embed=embed)

        await self.update_player_stat(user, 'tokens', -100, add_self=True)
    
    @commands.command(name="bigbox", aliases=['big'])
    async def open_big_box(self, ctx: Context):
        """Open a Big Box!"""
        user = ctx.author
        
        startokens = await self.get_player_stat(user, 'startokens')

        if startokens < 10:
            return await ctx.send("You do not have enough Star Tokens to open a brawl box.")
        
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        embed = await box.bigbox(self.config.user(user), user)

        await ctx.send(embed=embed)

        await self.update_player_stat(user, 'startokens', -10, add_self=True)
    
    async def get_player_stat(self, user: discord.User, stat: str, is_iter=False, substat: str = None):
        """Get stats of a player."""

        if not is_iter:
            return await getattr(self.config.user(user), stat)()

        async with getattr(self.config.user(user), stat)() as stat:
            if not substat:
                return stat
            else:
                return stat[substat]

    async def update_player_stat(self, user: discord.User, stat: str, 
                                                value, substat: str = None, sub_index=None, add_self=False):
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
            await stat_attr.set(value+old_val)

    def matchmaking(self, brawler_level: int):
        """Get an opponent!"""

        opp_brawler = random.choice(list(self.BRAWLERS))

        opp_brawler_level = random.randint(brawler_level-1, brawler_level+1)
        opp_brawler_sp = None

        if opp_brawler_level > 10:
            opp_brawler_level = 10
            opp_brawler_sp = random.randint(1, 2)

        if opp_brawler_level < 1:
            opp_brawler_level = 1

        return opp_brawler, opp_brawler_level, opp_brawler_sp

    async def get_trophies(self, user: discord.User, pb = False, brawler_name: str = None):
        """Get total trophies or trophies of a specified Brawler of an user.

        Returns total trophies if a brawler is not specified.
        """

        brawlers = await self.get_player_stat(user, "brawlers")

        stat = "trophies" if not pb else "pb"

        if not brawler_name:
            return sum([brawlers[brawler][stat] for brawler in brawlers])
        else:
            return brawlers[brawler_name][stat]

    async def brawl_rewards(self, user: discord.User, points: int, is_starplayer=False):
        """Adjust user variables and return embed containing reward."""

        if points > 0:
            reward_tokens = 20
            reward_xp = 8
            position = 1
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

        tokens = await self.get_player_stat(user, 'tokens')
        tokens_in_bank = await self.get_player_stat(user, 'tokens_in_bank')

        if reward_tokens > tokens_in_bank:
            reward_tokens = tokens_in_bank

        tokens_in_bank -= reward_tokens

        # brawler trophies
        selected_brawler = await self.get_player_stat(user, 'selected', is_iter=True, substat='brawler')
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True, substat=selected_brawler)
        trophies = brawler_data['trophies']

        reward_trophies = self.trophies_to_reward_mapping(
            trophies, '3v3', position)

        xp = await self.get_player_stat(user, 'xp')
        xp += reward_xp

        tokens += reward_tokens
        trophies += reward_trophies

        await self.update_player_stat(user, 'tokens', tokens)
        await self.update_player_stat(user, 'tokens_in_bank', tokens_in_bank)
        await self.update_player_stat(user, 'xp', xp)
        await self.update_player_stat(user, 'brawlers', trophies,
                                      substat=selected_brawler, sub_index='trophies')
        await self.handle_pb(user, selected_brawler)

        user_avatar = user.avatar_url

        embed = discord.Embed(colour=0xFFFFFF, title="Rewards")
        embed.set_author(name=user.name, icon_url=user_avatar)

        reward_xp_str = f"{f'{reward_xp} (Star Player)' if is_starplayer else f'{reward_xp}'}"

        embed.add_field(name="Trophies", value=f"{emojis['trophies']} {reward_trophies}")
        embed.add_field(name="Tokens", value=f"{emojis['token']} {reward_tokens}")
        embed.add_field(name="Experience", value=f"{emojis['xp']} {reward_xp_str}")

        rank_up = await self.handle_rank_ups(user, selected_brawler)
        trophy_road_reward = await self.handle_trophy_road(user)
        
        return embed, rank_up, trophy_road_reward

    def trophies_to_reward_mapping(self, trophies: int, game_type="3v3", position=1):

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

        # xp = await self.config.user(ctx.author).xp()
        # lvl = await self.config.user(ctx.author).lvl()

        xp = await self.get_player_stat(user, 'xp')
        lvl = await self.get_player_stat(user, 'lvl')

        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        if xp >= next_xp:
            carry = xp - next_xp
        else:
            return False

        await self.update_player_stat(user, 'xp', carry)
        await self.update_player_stat(user, 'lvl', lvl+1)

        level_up_msg = f"Level up! You have reached level {lvl+1}."

        tokens_reward = self.XP_LEVELS[str(lvl)]["TokensRewardCount"]
        reward_msg = f"Rewards: {tokens_reward} {emojis['token']}"

        tokens = await self.get_player_stat(user, 'tokens')
        tokens += tokens_reward
        await self.update_player_stat(user, 'tokens', tokens)

        return (level_up_msg, reward_msg)

    async def handle_pb(self, user: discord.User, brawler: str):
        """Handle personal best changes."""

        # individual brawler 
        trophies = await self.get_trophies(user=user, brawler_name=brawler)
        pb = await self.get_trophies(user=user, pb=True, brawler_name=brawler)

        if trophies > pb:
            await self.update_player_stat(user, 'brawlers', trophies, substat=brawler, sub_index='pb')
        
        # total trophies 
        # total_trophies = await self.get_trophies(user)
        # total_pb = await self.get_trophies(user=user, pb=True)

        # if total_trophies > total_pb:
        #     await self.up

    async def update_token_bank(self):
        """Task to update token banks."""
        while True:
            for user in self.bot.users:
                tokens_in_bank = await self.get_player_stat(user, 'tokens_in_bank')
                if tokens_in_bank == 200:
                    continue
                tokens_in_bank += 20
                if tokens_in_bank > 200:
                    tokens_in_bank = 200

                bank_update_timestamp = await self.get_player_stat(user, 'bank_update_ts')
                
                if not bank_update_timestamp:
                    continue

                bank_update_ts = datetime.utcfromtimestamp(ceil(bank_update_timestamp))
                time_now = datetime.utcnow()
                delta = time_now - bank_update_ts
                delta_min = delta.total_seconds() / 60

                if delta_min >= 80:
                    await self.update_player_stat(user, 'tokens_in_bank', tokens_in_bank)
                    epoch = datetime(1970, 1, 1)

                    # get timestamp in UTC 
                    timestamp = (time_now - epoch).total_seconds()
                    await self.update_player_stat(user, 'bank_update_ts', timestamp)

            await asyncio.sleep(60)

    def get_rank(self, pb):
        """Return rank of the Brawler based on its personal best."""

        for rank in self.RANKS:
            start = self.RANKS[rank]["ProgressStart"]
            end = start + self.RANKS[rank]["Progress"]  # 1 is not subtracted as we're calling range 
            if pb in range(start, end):
                return int(rank)
        else:
            return 35
    
    async def handle_rank_ups(self, user: discord.User, brawler: str):
        """Function to handle rank ups. 
        
        Returns an embed containing rewards if a brawler rank ups.
        """
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True, substat=brawler)
        
        pb = brawler_data['pb']
        rank = brawler_data['rank']

        rank_as_per_pb = self.get_rank(pb)

        if rank_as_per_pb > rank:
            await self.update_player_stat(user, 'brawlers', rank_as_per_pb, brawler, 'rank')
            
            rank_up_tokens = self.RANKS[str(rank)]["PrimaryLvlUpRewardCount"]
            rank_up_starpoints = self.RANKS[str(rank)]["SecondaryLvlUpRewardCount"]

            await self.update_player_stat(user, 'tokens', rank_up_tokens, add_self=True)
            await self.update_player_stat(user, 'starpoints', rank_up_starpoints, add_self=True)

            embed = discord.Embed(color=0xFFA232, title=f"Brawler Rank Up! {rank} → {rank_as_per_pb}")
            embed.set_author(name=user.name, icon_url=user.avatar_url)
            embed.add_field(name="Brawler", value=f"{brawler_emojis[brawler]} {brawler}")
            embed.add_field(name="Tokens", value=f"{emojis['token']} {rank_up_tokens}")
            if rank_up_starpoints:
                embed.add_field(name="Star Points", 
                            value=f"{emojis['starpoints']} {rank_up_starpoints}")
            return embed
        else:
            return False
    
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
                
                reward_name, reward_emoji, reward_str = self.tp_reward_strings(self.TROPHY_ROAD[tier], tier)
                
                desc = "Claim the reward by using the `-rewards` command!"
                embed = discord.Embed(color=0xFFA232, title="Trophy Road Reward", description=desc)
                embed.set_author(name=user.name, icon_url=user.avatar_url)
                embed.add_field(name=reward_name, value=f"{reward_emoji} {reward_str}")

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
            await self.update_player_stat(user, 'gold', reward_count, add_self=True)
        
        elif reward_type == 3:
            async with self.config.user(user).brawlers() as brawlers:
                brawlers[reward_extra] = default_stats
        
        elif reward_type == 6:
            async with self.config.user(user).boxes() as boxes:
                boxes['brawl'] += reward_count
            
            brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True)

            brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True)

            box = Box(self.BRAWLERS, brawler_data)
            embed = await box.brawlbox(self.config.user(user), user)

            await ctx.send(embed=embed)
        
        elif reward_type == 7:
            await self.update_player_stat(user, 'tickets', reward_count, add_self=True)
        
        elif reward_type == 9:
            await self.update_player_stat(user, 'token_doubler', reward_count, add_self=True)
        
        elif reward_type == 10:
            async with self.config.user(user).boxes() as boxes:
                boxes['mega'] += reward_count
        
        elif reward_type == 12:
            await ctx.send("Enter the name of Brawler to add powerpoints to:")
            pred = await self.bot.wait_for("message", check=MessagePredicate.same_context(ctx))
            
            brawler = pred.content
            # for users who input 'el_primo'
            brawler = brawler.replace("_", " ")
            
            brawler = brawler.title()

            user_brawlers = await self.get_player_stat(user, 'brawlers', is_iter=True)
            
            if brawler not in brawlers:
                return await ctx.send(f"You do not own {brawler}!")
            
            total_powerpoints = (await self.get_player_stat(user, 'brawlers', 
                        is_iter=True, substat=brawler))['total_powerpoints']

            if total_powerpoints == Box.max_pp:
                return await ctx.send(f"{brawler} can not recieve more powerpoints.")
            elif total_powerpoints + reward_count > Box.max_pp:
                return await ctx.send(f"{brawler} can not recieve {reward_count} powerpoints.")
            else:
                pass
            
            await self.update_player_stat(user, 'brawlers', reward_count, substat=brawler, 
                                                sub_index='powerpoints', add_self=True)
            await self.update_player_stat(user, 'brawlers', reward_count, substat=brawler, 
                                                sub_index='total_powerpoints', add_self=True)
        
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

        async with self.config.user(user).tpstored() as tpstored:
            tpstored.remove(reward_number)
        
    def check_if_win(self, first_player, second_player, first_health, 
            second_health, first_gems, second_gems):
        if (second_health <= 0 and first_health > 0) or (first_gems >= 10 and second_gems < 10):
            winner = first_player
            loser = second_player
        elif (first_health <= 0 and second_health > 0) or (second_gems >= 10 and first_gems < 10):
            winner = second_player
            loser = first_player
        elif (first_health <= 0 and second_health <= 0) or (second_gems >= 10 and first_gems >= 10):
            winner = None
            loser = None
        else:
            winner = False
            loser = False

        return winner, loser
    
    async def gemgrab(self, ctx, first: Brawler, second: Brawler, first_player, second_player, 
                first_brawler, second_brawler, fp_brawler_level, sp_brawler_level):
        """Function to play Gem Grab!"""
        
        guild = ctx.guild
        
        sfh = first._health(fp_brawler_level) # static first health
        ssh = second._health(sp_brawler_level) # static second health
        
        first_health = sfh
        second_health = ssh

        first_gems = 0
        second_gems = 0
        
        first_attacks = 0
        second_attacks = 0
        
        first_invincibility = False
        second_invincibility = False

        first_spawn = None
        second_spawn = None
        
        try:
            first_spawn_str = spawn_text[first_brawler]
        except:
            first_spawn_str = ""
        
        try:
            second_spawn_str = spawn_text[second_brawler]
        except:
            second_spawn_str = ""
        
        while True:
            
            if second_player != guild.me:
                try:
                    await second_player.send("Waiting for opponent to pick a move...")
                except:
                    return await ctx.send(f"{first_player.mention} {second_player.mention} Brawl cancelled."
                    f" Reason: {second_player.name} rejected the challenge.")
                
            if first_attacks >= 6:
                first_can_super = True
                end = 4
            else:
                first_can_super = False
                end = 3
            if second_spawn:
                end += 1

        
            if first_player != guild.me:
                desc = "Pick a move by typing the corresponding move number below."
                embed = discord.Embed(color=0xFFA232, title=f"Brawl against {second_player.name}")
                embed.set_author(name=first_player.name, icon_url=first_player.avatar_url)

                embed.add_field(name="Your Brawler", value=f"{brawler_emojis[first_brawler]} {first_brawler}")
                embed.add_field(name="Your Health", value=f"{emojis['health']} {int(first_health)}")
                embed.add_field(name="Your Gems", value=f"{gamemode_emotes['Gem Grab']} {first_gems}")
                
                if first_spawn:
                    embed.add_field(name=f"Your {first_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(first_spawn)}", inline=False)
                
                embed.add_field(name="Opponent's Brawler", value=f"{brawler_emojis[second_brawler]} {second_brawler}")
                embed.add_field(name="Opponent's Health", value=f"{emojis['health']} {int(second_health)}")
                embed.add_field(name="Opponent's Gems", value=f"{gamemode_emotes['Gem Grab']} {second_gems}")

                if second_spawn:
                    embed.add_field(name=f"Opponent's {second_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(second_spawn)}", inline=False)
                
                moves = (f"1. Attack\n2. Collect gem\n3. Dodge next move"
                            f"\n{'4. Use Super' if first_can_super else ''}").strip()
                
                if first_can_super and not second_spawn:
                    moves = "1. Attack\n2. Collect gem\n3. Dodge next move\n4. Use Super"
                elif first_can_super and second_spawn:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move\n4. Use Super\n5. Attack {second_spawn_str}"
                elif not first_can_super and second_spawn:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move\n4. Attack enemy {second_spawn_str}"
                else:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move"

                embed.add_field(name="Available Moves", value=moves, inline=False)

                try:
                    msg = await first_player.send(embed=embed)

                    react_emojis = ReactionPredicate.NUMBER_EMOJIS[1:end+1]
                    start_adding_reactions(msg, react_emojis)

                    pred = ReactionPredicate.with_emojis(react_emojis, msg)
                    await ctx.bot.wait_for("reaction_add", check=pred)

                    # pred.result is  the index of the letter in `emojis`

                    choice = pred.result + 1
                except:
                    return await ctx.send(f"{first_player.mention} {second_player.mention}" 
                            f"Reason: Unable to DM {first_player.name}. DMs are required to brawl!")

            else:
                # develop bot logic
                choice = random.randint(1, end)
            
            if choice == 1:
                damage = first._attack(fp_brawler_level)
                if not second_invincibility:
                    second_health -= damage
                    first_attacks += 1
                else:
                    second_invincibility = False
            elif choice == 2:
                first_gems += 1
                if second_invincibility:
                    second_invincibility = False
            elif choice == 3:
                first_invincibility = True
                if second_invincibility:
                    second_invincibility = False
            elif choice == 4:
                if first_can_super:
                    damage, first_spawn = first._ult(fp_brawler_level)
                    first_attacks = 0
                    if not second_invincibility:
                        second_health -= damage
                    else:
                        second_health -= damage * 0.5
                        second_invincibility = False
                else:
                    second_spawn -= first._attack(fp_brawler_level)
            elif choice == 5:
                second_spawn -= first._attack(fp_brawler_level)
            
            if first_spawn:
                damage = first._spawn(fp_brawler_level)
                if not second_invincibility:
                    second_health -= damage
                    first_attacks += 1
                else:
                    second_invincibility = False

            winner, loser = self.check_if_win(first_player, second_player, first_health, 
                    second_health, first_gems, second_gems)
            
            if winner == False:
                pass
            else:
                break
            
            if first_player != guild.me:
                await first_player.send("Waiting for opponent to pick a move...")
            
            if second_attacks >= 6:
                second_can_super = True
                end = 4
            else:
                second_can_super = False
                end = 3

            if second_player != guild.me:
                desc = "Pick a move by typing the corresponding move number below."
                embed = discord.Embed(color=0xFFA232, title=f"Brawl against {first_player.name}")
                embed.set_author(name=second_player.name, icon_url=second_player.avatar_url)
                
                embed.add_field(name="Your Brawler", value=f"{brawler_emojis[second_brawler]} {second_brawler}")
                embed.add_field(name="Your Health", value=f"{emojis['health']} {int(second_health)}")
                embed.add_field(name="Your Gems", value=f"{gamemode_emotes['Gem Grab']} {second_gems}")
                
                if second_spawn:
                    embed.add_field(name=f"Your {second_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(second_spawn)}", inline=False)
                
                embed.add_field(name="Opponent's Brawler", value=f"{brawler_emojis[first_brawler]} {first_brawler}")
                embed.add_field(name="Opponent's Health", value=f"{emojis['health']} {int(first_health)}")
                embed.add_field(name="Opponent's Gems", value=f"{gamemode_emotes['Gem Grab']} {first_gems}")
                
                if first_spawn:
                    embed.add_field(name=f"Opponent's {first_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(first_spawn)}", inline=False)
                
                if second_can_super and not first_spawn:
                    moves = "1. Attack\n2. Collect gem\n3. Dodge next move\n4. Use Super"
                elif second_can_super and first_spawn:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move\n4. Use Super\n5. Attack {first_spawn_str}"
                elif not second_can_super and first_spawn:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move\n4. Attack enemy {first_spawn_str}"
                else:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move"
                
                embed.add_field(name="Available Moves", value=moves, inline=False)

                msg = await second_player.send(embed=embed)

                react_emojis = ReactionPredicate.NUMBER_EMOJIS[1:end+1]
                start_adding_reactions(msg, react_emojis)

                pred = ReactionPredicate.with_emojis(react_emojis, msg)
                await ctx.bot.wait_for("reaction_add", check=pred)

                # pred.result is  the index of the letter in `emojis`

                choice = pred.result + 1

            else:
                # develop bot logic
                choice = random.randint(1, end)

            if choice == 1:
                damage = second._attack(sp_brawler_level)
                if not first_invincibility:
                    first_health -= damage
                    second_attacks += 1
                else:
                    first_invincibility = False
            elif choice == 2:
                second_gems += 1
                if first_invincibility:
                    first_invincibility = False
            elif choice == 3:
                second_invincibility = True
                if first_invincibility:
                    first_invincibility = False
            elif choice == 4:
                if second_can_super:
                    damage, second_spawn = second._ult(sp_brawler_level)
                    second_attacks = 0
                    if not first_invincibility:
                        first_health -= damage
                    else:
                        first_health -= damage * 0.5
                        first_invincibility = False
                else:
                    first_spawn -= second._attack(sp_brawler_level)
            elif choice == 5:
                first_spawn -= second._attack(sp_brawler_level)

            if second_spawn:
                damage = second._spawn(sp_brawler_level)
                if not first_invincibility:
                    first_health -= damage
                    second_attacks += 1
                else:
                    second_invincibility = False
            
            winner, loser = self.check_if_win(first_player, second_player, first_health, 
                    second_health, first_gems, second_gems)
            
            if winner == False:
                pass
            else:
                break
         
        return winner, loser
    
    @commands.command(name="tokens")
    @checks.is_owner()
    async def tokens(self, ctx: Context, user: discord.User = None):
        if not user:
            user = ctx.author
        
        await self.update_player_stat(user, 'tokens', 1000)
        await self.update_player_stat(user, 'startokens', 1000)
        
        async with self.config.user(user).brawlers() as brawlers:
            brawlers.pop('Rico', None)
            brawlers.pop('El Primo', None)
            brawlers.pop('Barley', None)
    
    @commands.command(name="max")
    @checks.is_owner()
    async def max_shelly(self, ctx: Context, user: discord.User = None):
        if not user:
            user = ctx.author
        
        await self.update_player_stat(user, 'brawlers', 1410, substat="Shelly", sub_index="total_powerpoints")
        await self.update_player_stat(user, 'brawlers', 10, substat="Shelly", sub_index="level")
        await self.update_player_stat(user, 'brawlers', 0, substat="Shelly", sub_index="powerpoints")
        await self.update_player_stat(user, 'brawlers', True, substat="Shelly", sub_index="sp1")
        await self.update_player_stat(user, 'brawlers', False, substat="Shelly", sub_index="sp2")
    
    def cog_unload(self):
        self.bank_update_task.cancel()
    
    __unload = cog_unload
