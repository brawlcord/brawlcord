import discord

class GameSession:
    """A class to represent and hold current game sessions per server."""

    timer: int
    guild: discord.Guild
    message_id: int
    reacted: bool = False
    teamred: Set[discord.Member] = set()
    teamblue: Set[discord.Member] = set()

    def __init__(self, **kwargs):
        self.guild: dict = kwargs.pop("guild")
        self.timer: int = kwargs.pop("timer")
        self.reacted = False
        self.message_id = 0
        teamred: Set[discord.Member] = set()
        teamblue: Set[discord.Member] = set()


class Box:
    """"""