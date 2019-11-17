import json
import random

import discord

# credits to Star List, developed by Henry
brawler_url = "https://www.starlist.pro/brawlers/detail/{}"
brawler_thumb = "https://www.starlist.pro/assets/brawler/{}.png"

emojis = {
    "powerpoint": "<:PowerPoint:645333239103488029>",
    "trophies": "<:bstrophy:645337311114035231>",
    "health": "<:health:645341012297777203>",
    "damage": "<:damage:645341012230668359>",
    "super": "<:super:645341012457422878>",
    "pb": "<:pb:645340943956049981>",
    "speed": "<:speed:645341012654293023>",
    "info": "<:info:645341012448903168>",
    "xp": "<:xp:645337312431046657>"
}

sp_icons = {
    "Shelly": ["<:ShellShock:645349547127603246>", "<:BandAid:645349544837644322>"]
}

rarity_colors = {
    "Trophy Road": 0x6db2ba,
    "Rare": 0x00d635,
    "Super Rare": 0x0060ac,
    "Epic": 0xa80564,
    "Mythic": 0xe20000,
    "Legendary": 0xf2da02
}

# image_urls = {
#     "powerpoint": "https://cdn.discordapp.com/emojis/645333239103488029.png?v=1"
# }

class Brawler:
    """Class to represent a Brawler."""

    name: str
    desc: str
    health: int
    attack: dict = {}
    speed: int
    rarity: str
    unlockTrp: int  # for trophy road brawlers only 
    ult: dict = {}
    sp1: dict = {}
    sp2: dict = {}

    def __init__(self, raw_data: dict, brawler: str):
        
        data = raw_data[brawler]

        self.name = brawler
        self.desc = data["desc"]
        self.health = data["health"]
        self.attack = data["attack"]
        self.speed = data["speed"]
        self.rarity = data["rarity"]
        self.unlockTrp = data["unlockTrp"]
        self.ult = data["ult"]
        self.sp1 = data["sp1"]
        self.sp2 = data["sp2"]

    def get_stat(self, stat, substat: str = None):
        """Get specific Brawler stat."""
        if substat:
            return getattr(self, stat)[substat]
        else:
            return getattr(self, stat)
    
    def get_all_stats(self):
        """Get all Brawler stats."""
        stats = {
            "health": self.health,
            "attack": self.attack,
            "speed": self.speed,
            "rarity": self.rarity,
            "unlockTrp": self.unlockTrp,
            "ult": self.ult,
            "sp1": self.sp1,
            "sp2": self.sp2,
        }

        return stats

    def _health(self, level):
        """Function to get health of Brawler of specified power level."""
        stats = self.buff_stats(level)

        return stats['health']
    
    def _attack(self, level):
        """Function to represent the attack of the Brawler. """
        pass
        
    def _ult(self, level):
        """Function to represent the Super of the Brawler."""
        pass

    def _sp1(self):
        """Function to represent the first SP of the Brawler."""
        pass

    def _sp2(self):
        """Function to represent the second SP of the Brawler."""
        pass

    def buff_stats(self, stats: dict, level: int):
        """Get Brawler stats by specified level."""

        if level == 10:
            level = 9
        
        upd_stats = {}

        for stat in stats:
            upgrader = stats[stat]/20
            stats[stat] += int(upgrader * (level - 1))
            # upd_stats[stat] = stats[stat]
            # upd_stats.append(stat)
        
        return stats

    def brawler_info(self, brawler_name: str, trophies:int, pb:int, level: int, 
            pp: int, next_level_pp: int, sp1 = False, sp2 = False):
        """Display brawler info in a formatted way."""

        # trophies_str = f"\n\n**Trophies:** {emojis['trophies']} {trophies} | **Personal Best:** {emojis['pb']} {pb}"

        # power = f"\n\n**Power:** {level} | {emojis['powerpoint']} **{pp}**/**{next_level_pp}**"

        # description = self.desc + trophies_str + power 
        url = brawler_url.format(brawler_name)

        embed = discord.Embed(color=rarity_colors[self.rarity], title=brawler_name, 
            description=self.desc, url=url)
        embed.set_thumbnail(url=brawler_thumb.format(brawler_name.title()))
        embed.add_field(name="POWER", value=f"{emojis['xp']} {level}")
        embed.add_field(name="POWER POINTS", value=f"{emojis['powerpoint']} {pp}/{next_level_pp}")
        embed.add_field(name="TROPHIES", value=f"{emojis['trophies']} {trophies}")
        embed.add_field(name="PERSONAL BEST", value=f"{emojis['pb']} {pb}")
        # embed.set_author(name=f"Power {level} - {pp}/{next_level_pp}", icon_url=image_urls['powerpoint'])
        return embed


class Shelly(Brawler):
    """A class to represent Shelly."""
    
    def _attack(self, level):
        """Function to represent the attack of the Brawler. """
        
        # getting all values 
        name = self.attack["name"]
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.7

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw
        elif chance >= 6:
            return raw * 0.7
        elif chance >= 4:
            return raw * 0.5
        elif chance >= 2:
            return raw * 0.3
        else:
            return 0

    def _ult(self, level):
        """Function to represent the Super of the Brawler. """

        # getting all values 
        name = self.ult["name"]
        damage = self.ult["damage"]
        ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.7

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw
        elif chance >= 6:
            return raw * 0.7
        elif chance >= 4:
            return raw * 0.5
        elif chance >= 2:
            return raw * 0.3
        else:
            return 0

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(self, brawler_name, trophies, pb, level, pp, next_level_pp, sp1=False, sp2=False):
        embed = super().brawler_info(brawler_name, trophies, pb, level, pp, next_level_pp, sp1=sp1, sp2=sp2)

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per shell: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per shell: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        if sp1:
            u1 = True
        if sp2:
            u2 = True
        
        sp_str = (f"{sp_icons['Shelly'][0]} **{self.sp1['name']}**\n> {self.sp1['desc']}"
                            f"\n{sp_icons['Shelly'][1]} **{self.sp2['name']}**\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Nita(Brawler):
    pass


class Colt(Brawler):
    pass
