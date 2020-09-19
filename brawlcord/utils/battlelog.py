from datetime import datetime

import discord
from redbot.core.bot import Red

from .core import utc_timestamp


class PartialBattleLogEntry:
    """Represents a partial battle log.

    It does not contain information about brawler trophies and rewards. It also
    does not have `timestamp` attribute.

    Parameters
    -------------
    player: `Player`
        The player the log is saved for.
    opponent: `Player`
        The opponent in the brawl.
    game_str: `str`
        Name of the game mode.
    result: `bool`
        Result of the brawl. True if player won, False if lost and None if draw.

    Attributes
    -------------
    player: `discord.User`
        The player the log is saved for.
    player_brawler_name: `str`
        Name of player's brawler.
    player_brawler_level: `int`
        Level of player's brawler.
    opponent: `discord.User`
        The opponent in the brawl.
    opponent_brawler_name: `str`
        Name of opponent's brawler.
    opponent_brawler_level: `int`
        Level of opponent's brawler.
    game_mode: `str`
        Name of the game mode.
    result: `str`
        Result of the brawl for player.
    """

    def __init__(self, player=None, opponent=None, game_mode: str = None, result: bool = None):
        if player and opponent and game_mode:
            self.player: discord.User = player.player
            self.player_brawler_name: str = player.brawler_name
            self.player_brawler_level: int = player.brawler_level

            self.opponent: discord.User = opponent.player
            self.opponent_brawler_name: str = opponent.brawler_name
            self.opponent_brawler_level: int = opponent.brawler_level

            self.game_mode = game_mode

            if result is True:
                self.result = "Victory"
            elif result is False:
                self.result = "Loss"
            else:
                self.result = "Draw"

    def to_json(self) -> dict:
        """Return a dictionary representing the `PartialBattleLogEntry` object."""

        return {
            "player_id": self.player.id,
            "player_brawler_name": self.player_brawler_name,
            "player_brawler_level": self.player_brawler_level,
            "opponent_id": self.opponent.id,
            "opponent_brawler_name": self.opponent_brawler_name,
            "opponent_brawler_level": self.opponent_brawler_level,
            "game_mode": self.game_mode,
            "result": self.result,
        }

    @classmethod
    async def from_json(cls, data: dict, bot: Red):
        """Return a `BattleLog` object from dictionary representation of the log."""

        self = cls()

        # Get player's `User` instance.
        self.player = bot.get_user(data["player_id"])
        if self.player is None:
            self.player = await bot.fetch_user(data["player_id"])

        self.player_brawler_name = data["player_brawler_name"]
        self.player_brawler_level = data["player_brawler_level"]

        # Get opponent's `User` instance.
        self.opponent = bot.get_user(data["opponent_id"])
        if self.opponent is None:
            self.opponent = await bot.fetch_user(data["opponent_id"])

        self.opponent_brawler_name = data["opponent_brawler_name"]
        self.opponent_brawler_level = data["opponent_brawler_level"]

        self.game_mode = data["game_mode"]
        self.result = data["result"]

        return self


class BattleLogEntry:
    """Represents a complete battle log entry.

    Parameters
    -------------
    partial_log: `Optional[PartialBattleLogEntry]`
        The partial log entry created for this brawl.
    player_extras: `Optional[Dict]`
        Extra properties related to the player.
    opponent_extras: `Optional[Dict]`
        Extra properties related to the opponent.

    `player_extras` and `opponent_extras` should contain the following keys:
        `brawler_trophies`
        `reward_trophies`

    Attributes
    -------------
    player: `discord.User`
        The player the log is saved for.
    player_brawler_name: `str`
        Name of player's brawler.
    player_brawler_level: `int`
        Level of player's brawler.
    player_brawler_trophies: `int`
        Trophies of player's brawler.
    player_reward_trophies: `int`
        Reward trophies of the player.
    opponent: `discord.User`
        The opponent in the brawl.
    opponent_brawler_name: `str`
        Name of opponent's brawler.
    opponent_brawler_level: `int`
        Level of opponent's brawler.
    opponent_brawler_trophies: `int`
        Trophies of opponent's brawler.
    opponent_reward_trophies: `int`
        Reward trophies of the opponent.
    timestamp: `float`
        Timestamp of the brawl.
    game_mode: `str`
        Name of the game mode.
    result: `str`
        Result of the brawl for player.
    """

    def __init__(
        self,
        partial_log: PartialBattleLogEntry = None,
        player_extras: dict = None,
        opponent_extras: dict = None
    ):
        if partial_log and player_extras and opponent_extras:
            # Get data from `partial_log`.
            self.player = partial_log.player
            self.player_brawler_name = partial_log.player_brawler_name
            self.player_brawler_level = partial_log.player_brawler_level

            self.opponent = partial_log.opponent
            self.opponent_brawler_name = partial_log.opponent_brawler_name
            self.opponent_brawler_level = partial_log.opponent_brawler_level

            self.game_mode = partial_log.game_mode
            self.result = partial_log.result

            # New data.
            self.timestamp = utc_timestamp(datetime.utcnow())

            self.player_brawler_trophies: int = player_extras["brawler_trophies"]
            self.player_reward_trophies: int = player_extras["reward_trophies"]

            self.opponent_brawler_trophies: int = opponent_extras["brawler_trophies"]
            self.opponent_reward_trophies: int = opponent_extras["reward_trophies"]

    def to_json(self) -> dict:
        """Return a dictionary representing the `BattleLogEntry` object."""

        return {
            "player_id": self.player.id,
            "player_brawler_name": self.player_brawler_name,
            "player_brawler_level": self.player_brawler_level,
            "opponent_id": self.opponent.id,
            "opponent_brawler_name": self.opponent_brawler_name,
            "opponent_brawler_level": self.opponent_brawler_level,
            "game_mode": self.game_mode,
            "result": self.result,
            "timestamp": self.timestamp,
            "player_brawler_trophies": self.player_brawler_trophies,
            "player_reward_trophies": self.player_reward_trophies,
            "opponent_brawler_trophies": self.opponent_brawler_trophies,
            "opponent_reward_trophies": self.opponent_reward_trophies
        }

    @classmethod
    async def from_json(cls, data: dict, bot: Red):
        """Return a `BattleLogEntry` object from dictionary representation of the log entry."""

        self = cls()

        # Get player's `User` instance.
        self.player = bot.get_user(data["player_id"])
        if self.player is None:
            self.player = await bot.fetch_user(data["player_id"])

        self.player_brawler_name = data["player_brawler_name"]
        self.player_brawler_level = data["player_brawler_level"]

        # Get opponent's `User` instance.
        self.opponent = bot.get_user(data["opponent_id"])
        if self.opponent is None:
            self.opponent = await bot.fetch_user(data["opponent_id"])

        self.opponent_brawler_name = data["opponent_brawler_name"]
        self.opponent_brawler_level = data["opponent_brawler_level"]

        self.game_mode = data["game_mode"]
        self.result = data["result"]

        self.timestamp = data["timestamp"]

        self.player_brawler_trophies = data["player_brawler_trophies"]
        self.player_reward_trophies = data["player_reward_trophies"]

        self.opponent_brawler_trophies = data["opponent_brawler_trophies"]
        self.opponent_reward_trophies = data["opponent_reward_trophies"]

        return self
