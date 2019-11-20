from .brawlers import Brawler

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
    """A class to represent Boxes."""

    gold: int
    powerpoints: int
    powerpoints_stacks = int
    
    # odds
    resources_1: int
    rarees = 2.7103,
    superrares = 1.2218,
    epic = 0.5527
    mythic = 0.2521
    legendary = 0.1115
    starpower: int

    # variables to store possibilities data
    can_get_pp = {}
    can_get_sp = {}

    # number of powerpoints required to max
    max_pp = 1410
    
    def __init__(self, all_brawlers, brawler_data):        
        for brawler in brawler_data:
            # self.owned.append(brawler)
            total_powerpoints = brawler_data[brawler]['total_powerpoints']
            if total_powerpoints < self.max_pp:
                self.can_get_pp[brawler] = self.max_pp - total_powerpoints
            
            level = brawler_data[brawler]['level']
            if level >= 9:
                sp1 = brawler_data[brawler]['sp1']
                sp2 = brawler_data[brawler]['sp2']

                if sp1 == False and sp2 == True:
                    self.can_get_sp[brawler] = ['sp1']
                elif sp1 == True and sp2 == False:
                    self.can_get_sp[brawler] = ['sp2']
                elif sp1 == False and sp2 == False:
                    self.can_get_sp[brawler] = ['sp1', 'sp2']
                else:
                    pass

    def brawlbox(self):
        """"""


class GameModes:
    """A class to represent game modes."""
