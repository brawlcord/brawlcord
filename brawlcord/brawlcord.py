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

from .brawlers import emojis, brawler_emojis, sp_icons, rank_emojis, Brawler, brawler_thumb

from .utils import Box, default_stats, gamemode_emotes, spawn_text, brawlers_map, GameModes

from .brawlhelp import BrawlcordHelp, EMBED_COLOR


BaseCog = getattr(commands, "Cog", object)

log = logging.getLogger("red.brawlcord")

__version__ = "1.0.0"
__author__ = "Snowsee"

default = {
    "report_channel": None,
    "custom_help": True
}

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
        "3v3": [0, 0], # [wins, losses]
        "duo": [0, 0], # [wins, losses]
    },
    "boxes": {
        "brawl": 0,
        "big": 0,
        "mega": 0
    }
}

imgur_links = {
    "shelly_tut": "https://i.imgur.com/QfKYzso.png"
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


class Brawlcord(BaseCog, name="Brawlcord"):
    """Play a simple version of Brawl Stars on Discord."""

    def __init__(self, bot):
        self.bot = bot

        # self._brawl_countdown = {}
        self.sessions = {}
        self.tasks = {}
        self.locks = {}

        self.config = Config.get_conf(self, 1_070_701_001, force_registration=True)

        self.path = bundled_data_path(self)

        self.config.register_global(**default)
        self.config.register_user(**default_user)

        self.BRAWLERS: dict = None
        self.REWARDS: dict = None
        self.XP_LEVELS: dict = None
        self.RANKS: dict = None
        self.TROPHY_ROAD: dict = None
        self.LEVEL_UPS: dict = None
        self.GAMEMODES: dict = None

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
        level_ups_fp = bundled_data_path(self) / "level_ups.json"
        gamemodes_fp = bundled_data_path(self) / "gamemodes.json"

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
        with level_ups_fp.open("r") as f:
            self.LEVEL_UPS = json.load(f)
        with gamemodes_fp.open("r") as f:
            self.GAMEMODES = json.load(f)

        custom_help = await self.config.custom_help()
        if custom_help:
            self.bot._help_formatter = BrawlcordHelp(self.bot)

    # @commands.command(name="brawlcord")
    # async def _brawlcord(self, ctx: Context):
    #     """Show info about the bot"""
    #     embed = discord.Embed(color=EMBED_COLOR)
    #     embed.add_field(name="Author")

    @commands.command(name="brawl", aliases=["b"])
    @commands.guild_only()
    async def _brawl(self, ctx: Context, opponent: discord.User = None):
        """Brawl against other players"""
        guild = ctx.guild
        user = ctx.author

        g: GameModes = GameModes(ctx, user, opponent, self.config.user, self.BRAWLERS)
        
        try:
            first_player, second_player, winner, loser = await g.initialize(ctx)
        except Exception as exc:
            return await ctx.send(f"Error: '{exc}' with brawl. Please notify bot owner by using `-report` command!") 
        
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
        """Begin the tutorial"""

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
            color=EMBED_COLOR, title="Tutorial", description=desc)
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

    @commands.command(name="stats", aliases=["s", "stat"])
    async def _stats(self, ctx: Context):
        """Display your resource statistics"""

        user = ctx.author
        
        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name=f"{user.name}'s Resource Stats", icon_url=user.avatar_url)

        trophies = await self.get_trophies(user)
        embed.add_field(name="Trophies", value=f"{emojis['trophies']} {trophies:,}")

        pb = await self.get_trophies(user=user, pb=True)
        embed.add_field(name="Highest Trophies", value=f"{emojis['pb']} {pb:,}")

        xp = await self.get_player_stat(user, 'xp')
        lvl = await self.get_player_stat(user, 'lvl')
        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        embed.add_field(name="Experience Level", value=f"{emojis['xp']} {lvl} `{xp}/{next_xp}`")

        gold = await self.get_player_stat(user, 'gold')
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}")

        tokens = await self.get_player_stat(user, 'tokens')
        embed.add_field(name="Tokens", value=f"{emojis['token']} {tokens}")

        startokens = await self.get_player_stat(user, 'startokens')
        embed.add_field(name="Star Tokens", value=f"{emojis['startoken']} {startokens}")

        token_doubler = await self.get_player_stat(user, 'token_doubler')
        embed.add_field(name="Token Doubler", value=f"{emojis['tokendoubler']} {token_doubler}")

        gems = await self.get_player_stat(user, 'gems')
        embed.add_field(name="Gems", value=f"{emojis['gem']} {gems}")

        starpoints = await self.get_player_stat(user, 'starpoints')
        embed.add_field(name="Star Points", value=f"{emojis['starpoints']} {starpoints}")

        selected = await self.get_player_stat(user, 'selected', is_iter=True)
        brawler = selected['brawler']
        sp = selected['starpower']
        skin = selected['brawler_skin']
        gamemode = selected['gamemode']

        embed.add_field(name="Selected Brawler", 
                value=f"{brawler_emojis[brawler]} {skin if skin != 'Default' else ''} {brawler}"
                        f'''{f" - {emojis['spblank']} {sp}" if sp else ''}''', inline=False)
        embed.add_field(name="Selected Game Mode", 
                value=f"{gamemode_emotes[gamemode]} {gamemode}", inline=False)

        await ctx.send(embed=embed)
    
    @commands.command(name="profile", aliases=["p", "pro"])
    async def _profile(self, ctx: Context, user: discord.User = None):
        """Display your or specific user's profile"""

        if not user:
            user = ctx.author
        
        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name=f"{user.name}'s Profile", icon_url=user.avatar_url)

        trophies = await self.get_trophies(user)
        embed.add_field(name="Trophies", value=f"{emojis['trophies']} {trophies:,}")

        pb = await self.get_trophies(user=user, pb=True)
        embed.add_field(name="Highest Trophies", value=f"{emojis['pb']} {pb:,}")

        xp = await self.get_player_stat(user, 'xp')
        lvl = await self.get_player_stat(user, 'lvl')
        next_xp = self.XP_LEVELS[str(lvl)]["Progress"]

        embed.add_field(name="Experience Level", value=f"{emojis['xp']} {lvl} `{xp}/{next_xp}`")

        brawl_stats = await self.get_player_stat(user, 'brawl_stats', is_iter=True)

        wins_3v3 = brawl_stats["3v3"][0]
        wins_solo = brawl_stats["solo"][0]
        wins_duo = brawl_stats["duo"][0]

        embed.add_field(name="3 vs 3 Wins", value=f"{wins_3v3}")
        embed.add_field(name="Solo Wins", value=f"{gamemode_emotes['Solo Showdown']} {wins_solo}")
        embed.add_field(name="Duo Wins", value=f"{gamemode_emotes['Duo Showdown']} {wins_duo}")

        await ctx.send(embed=embed)
    
    @commands.command(name="brawler", aliases=['binfo'])
    async def _brawler(self, ctx: Context, *, brawler_name: str):
        """Show stats of a particular Brawler"""

        user = ctx.author
        
        brawlers = self.BRAWLERS

        # for users who input 'el_primo'
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
        
        owned_brawlers = await self.get_player_stat(user, 'brawlers', is_iter=True)

        owned = True if brawler in owned_brawlers else False

        b: Brawler = brawlers_map[brawler](self.BRAWLERS, brawler)

        if owned:
            brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True, substat=brawler)
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

            embed = b.brawler_info(brawler, trophies, pb, rank, level, pp, next_level_pp, sp1, sp2)

        else:
            embed = b.brawler_info(brawler)

        await ctx.send(embed=embed)
 
    @commands.command(name="brawlers")
    async def all_brawlers(self, ctx: Context, user: discord.User = None):
        """Show details of all the Brawlers"""
        if not user:
            user = ctx.author

        owned = await self.get_player_stat(ctx.author, 'brawlers', is_iter=True)
        
        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        # below code is to sort brawlers by their trophies 
        brawlers = {}
        for brawler in owned:
            brawlers[brawler] = owned[brawler]["trophies"]
        
        sorted_brawlers = dict(sorted(brawlers.items(), key=lambda x: x[1], reverse=True))

        for brawler in sorted_brawlers:
            level = owned[brawler]["level"]
            trophies = owned[brawler]["trophies"]
            pb = owned[brawler]["pb"]
            rank = owned[brawler]["rank"]

            embed.add_field(name=f"{brawler_emojis[brawler]} {brawler}", 
                value=(f"{emojis['spgrey']}`{trophies:>4}`{emojis['wintrophy']} |" 
                    f" {rank_emojis['br'+str(rank)]}`{pb:>4}`{emojis['powerplay']}PB"),
                inline=False)
        
        await ctx.send(embed=embed)  

    @commands.group(name="rewards", autohelp=False)
    async def _rewards(self, ctx: Context):
        """View and claim collected trophy road rewards"""
        pass            
    
    @_rewards.command(name="list")
    async def rewards_list(self, ctx: Context):
        """View collected trophy road rewards"""

        user = ctx.author
        
        tpstored = await self.get_player_stat(user, 'tpstored')

        desc = "Use `-rewards claim <reward_number>` or `-rewards claimall` to claim rewards!"
        embed = discord.Embed(color=EMBED_COLOR, title="Rewards List", description=desc)
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
        """Claim collected trophy road reward"""

        user = ctx.author
        
        tpstored = await self.get_player_stat(user, 'tpstored')

        if reward_number not in tpstored:
            return await ctx.send(f"You do not have {reward_number} collected.")
        
        await self.handle_reward_claims(ctx, reward_number)
        
        await ctx.send("Reward successfully claimed.")    
        
    @_rewards.command(name="claimall")
    async def rewards_claim_all(self, ctx: Context):
        """Claim all collected trophy road rewards"""
        user = ctx.author

        tpstored = await self.get_player_stat(user, 'tpstored')

        for tier in tpstored:
            await self.handle_reward_claims(ctx, tier)
        
        await ctx.send("Rewards successfully claimed.")    
    
    @commands.group(name="select", autohelp=False)
    async def _select(self, ctx: Context):
        """Change selected Brawler or game mode"""
        pass
    
    @_select.command(name="brawler", aliases=['b'])
    async def select_brawler(self, ctx: Context, *, brawler_name: str):
        """Change selected Brawler"""

        user_owned = await self.get_player_stat(ctx.author, 'brawlers', is_iter=True)

        # for users who input 'el_primo'
        brawler_name = brawler_name.replace("_", " ")

        brawler_name = brawler_name.title()

        if brawler_name not in user_owned:
            return await ctx.send(f"You do not own {brawler_name}!")
        
        await self.update_player_stat(ctx.author, 'selected', brawler_name, substat='brawler')
        
        brawler_data = await self.get_player_stat(ctx.author, 'brawlers', is_iter=True, substat=brawler_name)

        sps = [f"sp{ind}" for ind, sp in enumerate([brawler_data["sp1"], brawler_data["sp2"]], start=1) if sp]
        sps = [self.BRAWLERS[brawler_name][sp]["name"] for sp in sps]
        
        if sps:
            await self.update_player_stat(ctx.author, 'selected',  random.choice(sps), substat='starpower')
        else:
            await self.update_player_stat(ctx.author, 'selected',  None, substat='starpower')
        
        await ctx.send(f"Changed selected Brawler to {brawler_name}!")

    @_select.command(name="gamemode", aliases=['gm'])
    async def select_gamemode(self, ctx: Context, *, gamemode: str):
        """Change selected game mode"""

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
        """Get all emojis of the server"""

        guild = ctx.guild

        server_emojis = await guild.fetch_emojis()

        print("_emojis = {")
        for emoji in server_emojis:
            print(f"    \"{emoji.name}\": \"<:{emoji.name}:{emoji.id}>\",")
        print("}")
    
    @commands.command(name="brawlbox")
    async def open_brawl_box(self, ctx: Context):
        """Open a Brawl Box"""
        user = ctx.author
        
        tokens = await self.get_player_stat(user, 'tokens')

        if tokens < 100:
            return await ctx.send("You do not have enough Tokens to open a brawl box.")
        
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.brawlbox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(f"Error '{exc}'' while opening a Brawl Box. Please notify bot creator"
                " using `-report` command.")

        await ctx.send(embed=embed)

        await self.update_player_stat(user, 'tokens', -100, add_self=True)
    
    @commands.command(name="bigbox", aliases=['big'])
    async def open_big_box(self, ctx: Context):
        """Open a Big Box"""
        user = ctx.author
        
        startokens = await self.get_player_stat(user, 'startokens')

        if startokens < 10:
            return await ctx.send("You do not have enough Star Tokens to open a brawl box.")
        
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True)

        box = Box(self.BRAWLERS, brawler_data)
        try:
            embed = await box.bigbox(self.config.user(user), user)
        except Exception as exc:
            return await ctx.send(f"Error {exc} while opening a Big Box. Please notify bot creator"
                " using `-notify` command.")

        await ctx.send(embed=embed)

        await self.update_player_stat(user, 'startokens', -10, add_self=True)
    
    @commands.command(name="upgrade", aliases=['up'])
    async def upgrade_brawlers(self, ctx: Context, *, brawler: str):
        """Upgrade a Brawler"""
        user = ctx.author
        
        user_owned = await self.get_player_stat(user, 'brawlers', is_iter=True)

        # for users who input 'el_primo'
        brawler = brawler.replace("_", " ")

        brawler = brawler.title()

        if brawler not in user_owned:
            return await ctx.send(f"You do not own {brawler}!")
        
        brawler_data = await self.get_player_stat(user, 'brawlers', is_iter=True, substat=brawler)
        level = brawler_data['level']
        if level == 9:
            return await ctx.send("Brawler is already at level 9. Open boxes to collect Star Powers!")
        elif level == 10:
            return await ctx.send("Brawler is already at level 10. If you are missing a Star Power, then open boxes to collect it!")

        powerpoints = brawler_data['powerpoints']

        required_powerpoints = self.LEVEL_UPS[str(level)]["Progress"]

        if powerpoints < required_powerpoints:
            return await ctx.send(f"You do not have enough powerpoints! ({powerpoints}/{required_powerpoints})")
        
        gold = await self.get_player_stat(user, 'gold', is_iter=False)

        required_gold = self.LEVEL_UPS[str(level)]["RequiredCurrency"]

        if gold < required_gold:
            return await ctx.send(f"You do not have enough gold! ({gold}/{required_gold})")
        
        msg = await ctx.send(f"{user.mention} Upgrading {brawler} to power {level+1} will cost" 
            f" {emojis['gold']} {required_gold}. Continue?")
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result:
            # User responded with tick
            pass
        else:
            # User responded with cross
            return await ctx.send("Upgrade cancelled.")
        
        await self.update_player_stat(user, 'brawlers', level+1, substat=brawler, sub_index='level')
        await self.update_player_stat(user, 'brawlers', powerpoints-required_powerpoints, 
                substat=brawler, sub_index='powerpoints')
        await self.update_player_stat(user, 'gold', gold-required_gold)

        await ctx.send(f"Upgraded {brawler} to power {level+1}!")
    
    @commands.command(name="gamemodes", aliases=['gm', 'events'])
    async def _gamemodes(self, ctx: Context):
        """Show details of all the game modes"""

        user = ctx.author
        
        user_owned = await self.get_player_stat(user, 'gamemodes', is_iter=True)
        
        embed = discord.Embed(color=EMBED_COLOR, title="Game Modes")
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        
        for event_type in ["Team Event", "Solo Event", "Duo Event", "Ticket Event"]:
            embed_str = ""
            for gamemode in self.GAMEMODES:
                if event_type != self.GAMEMODES[gamemode]["event_type"]:
                    continue
                embed_str += f"\n{gamemode_emotes[gamemode]} {gamemode}"
                if gamemode not in user_owned:
                    embed_str += f" [Locked]"
            
            embed.add_field(name=event_type+"s", value=embed_str, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="report")
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.user)
    async def _report(self, ctx: Context, *, msg: str):
        """Send a report to the bot owner"""
        channel_id = await self.config.report_channel()
        
        report_str = (f"`{datetime.utcnow().replace(microsecond=0)}` {ctx.author}"
                    f" (`{ctx.author.id}`) reported from `{ctx.guild}`: **{msg}**")
        
        if channel_id:
            for guild in self.bot.guilds:
                try:
                    channel = discord.utils.get(guild.text_channels, id=channel_id)
                    break
                except:
                    pass
            await channel.send(report_str)
        else:
            owner = self.bot.get_user(self.bot.owner_id)
            await owner.send(report_str)
        
        await ctx.send("Thank you for sending a report. Your issue will be resolved as soon as possible.")
    
    @commands.command(name="rchannel")
    @checks.is_owner()
    async def report_channel(self, ctx: Context, channel: discord.TextChannel = None):
        """Set reports channel"""
        if not channel:
            channel = ctx.channel()
        await self.config.report_channel.set(channel.id)
        await ctx.send(f"Report channel set to {channel.mention}.")
    
    @commands.group(name="leaderboard", aliases=['lb'], autohelp=False)
    async def _leaderboard(self, ctx: Context):
        """Display the leaderboard"""

        if ctx.invoked_subcommand:
            return
        
        title = "Brawlcord Leaderboard - Highest Trophies"

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

        brawler_name = self.parse_brawler_name(brawler_name)
        
        if not brawler_name:
            return await ctx.send(f"{brawler_name} does not exist!")
        
        title = f"Brawlcord {brawler_name} Leaderboard"
        
        url=f"{brawler_thumb.format(brawler_name)}"

        await self.leaderboard_handler(ctx, title, url, 4, brawler_name=brawler_name)
  
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

        trophies += reward_trophies
        
        token_doubler = await self.get_player_stat(user, 'token_doubler')
        
        upd_td = token_doubler - reward_tokens

        if token_doubler > reward_tokens:
            reward_tokens *= 2
        else:
            reward_tokens += token_doubler
        
        await self.update_player_stat(user, 'tokens', reward_tokens, add_self=True)
        await self.update_player_stat(user, 'tokens_in_bank', tokens_in_bank)
        await self.update_player_stat(user, 'xp', reward_xp, add_self=True)
        await self.update_player_stat(user, 'brawlers', trophies,
                                      substat=selected_brawler, sub_index='trophies')
        await self.update_player_stat(user, 'token_doubler', upd_td)
        await self.handle_pb(user, selected_brawler)

        user_avatar = user.avatar_url

        embed = discord.Embed(color=EMBED_COLOR, title="Rewards")
        embed.set_author(name=user.name, icon_url=user_avatar)

        reward_xp_str = f"{f'{reward_xp} (Star Player)' if is_starplayer else f'{reward_xp}'}"

        embed.add_field(name="Trophies", value=f"{emojis['trophies']} {reward_trophies}")
        embed.add_field(name="Tokens", value=f"{emojis['token']} {reward_tokens}")
        embed.add_field(name="Experience", value=f"{emojis['xp']} {reward_xp_str}")

        if token_doubler > 0:
            embed.add_field(name="Token Doubler", value=f"{emojis['tokendoubler']} x{upd_td} remaining!")

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

            embed = discord.Embed(color=EMBED_COLOR, title=f"Brawler Rank Up! {rank} → {rank_as_per_pb}")
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
                embed = discord.Embed(color=EMBED_COLOR, title="Trophy Road Reward", description=desc)
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
        
    def get_sp_info(self, brawler_name: str, sp: str):
        """Return name and emoji of the Star Power."""

        for brawler in self.BRAWLERS:
            if brawler == brawler_name:
                sp_name = self.BRAWLERS[brawler][sp]
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
    
    async def leaderboard_handler(self, ctx: Context, title: str, thumb_url: str, padding: int, 
            pb=False, brawler_name=None):
        """Handler for all leaderboards."""

        all_users = await self.config.all_users()
        users = []
        for guild in self.bot.guilds:
            for user_id in all_users:
                try:
                    user = guild.get_member(user_id)
                    trophies = await self.get_trophies(user, pb=pb, brawler_name=brawler_name)
                    users.append((user, trophies))
                except:
                    pass
        
        # remove duplicates 
        users = list(set(users))
        users = sorted(users, key=lambda k: k[1], reverse=True)
        
        embed_desc = ""
        add_user = True
        # return first 10 (or fewer) members
        for i in range(10):
            try:    
                trophies = users[i][1]
                user = users[i][0]
                if user == ctx.author:
                    embed_desc += (f"\n**`{(i+1):02d}.`{emojis['wintrophy']}`{trophies:>{padding}}`"
                        f" {user.mention} - {user}**")
                    add_user = False
                else:
                    embed_desc += (f"\n`{(i+1):02d}.`{emojis['wintrophy']}`{trophies:>{padding}}`"
                        f" {user.mention} - {user}")
            except:
                pass

        embed = discord.Embed(color=EMBED_COLOR, description=embed_desc)
        embed.set_author(name=title, icon_url=ctx.guild.me.avatar_url)
        embed.set_thumbnail(url=thumb_url)
        
        # add rank of user
        if add_user:
            for idx, user in enumerate(users):
                if ctx.author == user['name']:
                    val_str = ""
                    for j in range(-1, 4):
                        if idx + j >= 0:
                            try:
                                trophies = users[idx+j][1]
                                user = users[idx+j][0]
                                if user == ctx.author:
                                    val_str += (f"\n**`{(idx+j+1):02d}.` {emojis['wintrophy']}"
                                        f"`{trophies:>{padding}}` {user.mention} - {user}**")
                                else:
                                    val_str += (f"\n`{(idx+j+1):02d}.` {emojis['wintrophy']}"
                                        f"`{trophies:>{padding}}` {user.mention} - {user}")
                            except:
                                pass
            try:
                embed.add_field(name="Your position", value=val_str)
            except UnboundLocalError:
                # happens only in case of brawlers 
                embed.add_field(name=f"\u200bNo one owns {brawler_name}!", 
                    value="Open boxes to unlock new Brawlers.")
            except:
                pass

        await ctx.send(embed=embed)
    
    @commands.command(name="tokens")
    @checks.is_owner()
    async def tokens(self, ctx: Context, user: discord.User = None):
        if not user:
            user = ctx.author
        
        await self.update_player_stat(user, 'tokens', 1000)
        await self.update_player_stat(user, 'startokens', 1000)
        
        await self.update_player_stat(user, 'gold', 3494)

        await self.update_player_stat(user, 'selected', "Shell Shock", substat="starpower")
        
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
    
    @commands.command(name="initstats")
    @checks.is_owner()
    async def init_stats(self, ctx: Context, user: discord.User = None):
        if not user:
            user = ctx.author
        
        await self.update_player_stat(user, 'brawl_stats', [0, 0], substat="solo")
        await self.update_player_stat(user, 'brawl_stats', [0, 0], substat="3v3")
        await self.update_player_stat(user, 'brawl_stats', [0, 0], substat="duo")
    
    def cog_unload(self):
        self.bank_update_task.cancel()
    
    __unload = cog_unload
