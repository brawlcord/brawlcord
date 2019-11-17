# Standard Library
import asyncio
import json
import logging
import random
import time

# Discord
import discord

# Redbot
from redbot.core import Config, commands
from redbot.core.commands.context import Context
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.common_filters import filter_various_mentions
from redbot.core.utils.menus import (DEFAULT_CONTROLS, menu,
                                     start_adding_reactions)
# from redbot.core.utils.chat_formatting import box
from redbot.core.utils.predicates import ReactionPredicate

from .brawlers import Brawler, Shelly, Nita, Colt


BaseCog = getattr(commands, "Cog", object)

log = logging.getLogger("red.brawlcord")

__version__ = "1.0.0"
__author__ = "Snowsee"

default_stats = {
    "trophies": 0,
    "pb": 0,
    "level": 1,
    "powerpoints": 0,
    "skins": ["Default"],
    "sp1": False,
    "sp2": False
}

default_user = {
    "exp": 0,
    "gold": 0,
    "lvl": 1,
    "starpoints": 0,
    "startokens": 0,
    "tokens": 0,
    "tokens_in_bank": 200,
    # "trophies": 0,
    "tutorial_finished": False,
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


class BrawlCord(BaseCog, name="Brawl Cord"):
    """Simulate Brawl Stars."""

    def __init__(self, bot):
        self.bot = bot

        # self._brawl_countdown = {}
        self.sessions = {}
        self.tasks = {}
        self.locks = {}

        self.config = Config.get_conf(
            self, 1_070_701_001, force_registration=True)

        self.path = bundled_data_path(self)

        self.config.register_user(**default_user)

        self.BRAWLERS = None

    async def initialize(self):
        brawlers_fp = bundled_data_path(self) / "brawlers.json"

        with brawlers_fp.open("r") as f:
            self.BRAWLERS = json.load(f)

    @commands.command(name="brawl", aliases=["b"])
    @commands.guild_only()
    # @commands.cooldown(rate=1, per=60, type=commands.BucketType.guild)
    async def _brawl(
        self,
        ctx: Context,
        teammate1: discord.Member = None,
        teammate2: discord.Member = None
    ):
        """Brawl against others!"""

        author = ctx.author
        guild = ctx.guild

        tutorial_finished = await self.get_player_stat(author, "tutorial_finished")

        if not tutorial_finished:
            return await ctx.send(f"{author.mention} You have not finished tutorial yet."
                                  "Use  `-tutorial` to start tutorial.")

        # teammates = {
        #     teammate1: False,
        #     teammate2: False
        # }

        # for teammate in teammates:
        #     if teammate:
        #         teammates[teammate] = True

        # await ctx.send(teammates)

        selected_brawler = (await self.get_player_stat(author, "selected"))["brawler"]

        user_brawler_level = (await self.get_player_stat(author, "brawlers"))[selected_brawler]["level"]

        opp_brawler, opp_brawler_level, opp_brawler_sp = self.matchmaking(user_brawler_level)

        user1: Brawler = brawlers_map[selected_brawler](self.BRAWLERS, selected_brawler)
        # opp1: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)
        opp1 = Shelly(self.BRAWLERS, "Shelly")

        # await ctx.send(embed=user1.brawler_info("Shelly", 10, 10, 5, 0, 200))

        user_health = user1._health(user_brawler_level)
        opp_health = opp1._health(opp_brawler_level)

        opp_health -= user1._attack(user_brawler_level)

        user_counter = 0
        opp_counter = 0

        winner = "Computer"

        while True:
            print(f"You before attack: {user_health}")
            print(f"Computer before attack: {opp_health}")
            if user_counter > 0 and user_counter % 5 == 0:
                res = user1._ult(user_brawler_level)
                opp_health -= res
                if res > 0:
                    user_counter += 1
            if opp_counter > 0 and opp_counter % 5 == 0:
                res = opp1._ult(opp_brawler_level)
                user_health -= res
                if res > 0:
                    opp_counter += 1
            
            else:
                res_u = user1._attack(user_brawler_level)
                res_o = opp1._attack(opp_brawler_level)

                if res_u > 0:
                    user_counter += 1
                if res_o > 0:
                    opp_counter += 1
                
                user_health -= res_o
                opp_health -= res_u
            
            print(f"You after attack: {user_health}")
            print(f"Computer after attack: {opp_health}")
            
            if user_health <= 0 and opp_health > 0:
                break
            if opp_health <= 0 and user_health > 0:
                winner = "User"
                break
            if opp_health <= 0 and user_health <= 0:
                winner = "Draw"
                break
            else:
                continue
            
        if winner == "Computer":
            await ctx.send(f"{author.mention} You lose!")
        elif winner == "User":
            await ctx.send(f"{author.mention} You win!")
        else:
            await ctx.send(f"{author.mention} The match ended as a draw!")
            

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

        desc = ("Hi, I'm Shelly! I'll introduce you to the world of BrawlCord."
                "Don't worry Brawler, it will only take a minute!")

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

        await self.config.user(author).tutorial_finished.set(True)

    # @commands.command(name="stat_test")
    # async def stat_test(self, ctx: Context):
    #     """"""
    #     s = Shelly(self.BRAWLERS, "Shelly")

    #     damage = s.get_stat("attack", "damage")

    #     return await ctx.send(damage)

    async def get_player_stat(self, user: discord.User, stat: str):
        """Get stats of a player."""
        # if not stat:
        #     return False

        return await getattr(self.config.user(user), stat)()

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

    async def get_trophies(self, user: discord.User, brawler_name: str = None):
        """Get total trophies or trophies of a specified Brawler of an user.

        Returns total trophies if a brawler is not specified.
        """

        brawlers = await self.get_player_stat(user, "brawlers")

        if not brawler_name:
            return sum([brawlers[brawler]["trophies"] for brawler in brawlers])
        else:
            return brawler_name[brawler_name]["trophies"]

    def buff_stats(self, brawler: Brawler, level: int):
        """Get Brawler stats by specified level."""

        # list of stats to buff
        stats_to_buff = [
            brawler.health,
            brawler.attack["damage"],
            brawler.ult["damage"]
        ]
