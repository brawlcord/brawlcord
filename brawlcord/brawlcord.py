import asyncio
import json
import logging
from abc import ABC

from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from redbot.core.commands import Context

from .brawlhelp import BrawlcordHelp
from .economy import EconomyMixin
from .gameplay import GameplayMixin
from .misc import MiscMixin
from .owner import OwnerMixin
from .stats import StatisticsMixin
from .tasks import TasksMixin
from .utils.constants import default_stats
from .utils.errors import MaintenanceError

__version__ = "2.3.1"
__author__ = "Snowsee"

old_info = None
old_invite = None

default = {
    "report_channel": None,
    "custom_help": True,
    "maintenance": {
        "duration": None,
        "setting": False
    },
    "shop_reset_ts": None,  # shop reset timestamp
    "st_reset_ts": None,  # star tokens reset timestamp
    "clubs": [],
    "club_id_length": 5,
    # Whether the bot has informed the bot owners about discontinuation of the Red cog or not.
    "informed_about_discontinuation": False,
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
    "cooldown": {},
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
        "solo": [0, 0],  # [wins, losses]
        "3v3": [0, 0],  # [wins, losses]
        "duo": [0, 0],  # [wins, losses]
    },
    # number of boxes collected from trophy road
    "boxes": {
        "brawl": 0,
        "big": 0,
        "mega": 0
    },
    # rewards added by the bot owner
    # can be adjusted to include brawlers, gamemodes, etc
    "gifts": {
        "brawlbox": 0,
        "bigbox": 0,
        "megabox": 0
    },
    "shop": {},
    # list of gamemodes where the user
    # already received daily star tokens
    "todays_st": [],
    "battle_log": [],
    "partial_battle_log": [],
    "club": None,  # club identifier
}

log = logging.getLogger("red.brawlcord")


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class Brawlcord(
    EconomyMixin,
    GameplayMixin,
    MiscMixin,
    OwnerMixin,
    StatisticsMixin,
    TasksMixin,
    commands.Cog,
    metaclass=CompositeMetaClass
):
    """Brawlcord is a Discord bot to play a simple version of Brawl Stars on Discord."""

    def __init__(self, bot: Red):
        super().__init__()

        self.bot = bot

        self.sessions = []

        self.config = Config.get_conf(
            self, 1_070_701_001, force_registration=True)

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
        self.LEAGUES: dict = None

        def error_callback(fut):
            try:
                fut.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logging.exception("Error in task", exc_info=exc)
                print("Error in task:", exc)

        self.bank_update_task = self.bot.loop.create_task(self.update_token_bank())
        self.status_task = self.bot.loop.create_task(self.update_status())
        self.shop_and_st_task = self.bot.loop.create_task(self.update_shop_and_st())
        self.bank_update_task.add_done_callback(error_callback)
        self.shop_and_st_task.add_done_callback(error_callback)
        self.status_task.add_done_callback(error_callback)

    async def initialize(self):
        brawlers_fp = bundled_data_path(self) / "brawlers.json"
        rewards_fp = bundled_data_path(self) / "rewards.json"
        xp_levels_fp = bundled_data_path(self) / "xp_levels.json"
        ranks_fp = bundled_data_path(self) / "ranks.json"
        trophy_road_fp = bundled_data_path(self) / "trophy_road.json"
        level_ups_fp = bundled_data_path(self) / "level_ups.json"
        gamemodes_fp = bundled_data_path(self) / "gamemodes.json"
        leagues_fp = bundled_data_path(self) / "leagues.json"

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
        with leagues_fp.open("r") as f:
            self.LEAGUES = json.load(f)

        custom_help = await self.config.custom_help()
        if custom_help:
            self.bot._help_formatter = BrawlcordHelp(self.bot)

        # Inform about Red discontinuation.
        if not await self.config.informed_about_discontinuation():
            await self.bot.send_to_owners(
                "Brawlcord is getting rewritten as a standalone bot in a different"
                " programming language. Therefore, the future versions of the bot will not"
                " be available as Red cogs. Additionally, the repo name of Brawlcord's Red cog"
                " has changed. Please see the following link to update the repo URL for your bot:"
                " https://brawlcord.github.io/discontinuing-red"
            )
            await self.config.informed_about_discontinuation.set(True)

    # This command needs to be in this class because of `old_info` variable.
    @commands.command(name="redinfo")
    async def red_info(self, ctx: Context):
        """Show info about Red"""

        global old_info
        if old_info:
            await ctx.invoke(old_info)

    async def cog_command_error(self, ctx: Context, error: Exception):
        if not isinstance(
            getattr(error, "original", error),
            (
                commands.UserInputError,
                commands.DisabledCommand,
                commands.CommandOnCooldown,
            ),
        ):
            if isinstance(error, MaintenanceError):
                await ctx.send(error)

        await ctx.bot.on_command_error(
            ctx, getattr(error, "original", error), unhandled_by_cog=True
        )

    def cog_unload(self):
        # Cancel various tasks.
        self.bank_update_task.cancel()
        self.status_task.cancel()
        self.shop_and_st_task.cancel()

        # Restore old invite command.
        global old_invite
        if old_invite:
            try:
                self.bot.remove_command("invite")
            except Exception:
                pass
            self.bot.add_command(old_invite)

        # Restore old invite command.
        global old_info
        if old_info:
            try:
                self.bot.remove_command("info")
            except Exception:
                pass
            self.bot.add_command(old_info)


async def setup(bot: Red):
    # Replace invite command.
    global old_invite
    old_invite = bot.get_command("invite")
    if old_invite:
        bot.remove_command(old_invite.name)

    # Replace info command.
    global old_info
    old_info = bot.get_command("info")
    if old_info:
        bot.remove_command(old_info.name)

    brawlcord = Brawlcord(bot)
    await brawlcord.initialize()
    bot.add_cog(brawlcord)
