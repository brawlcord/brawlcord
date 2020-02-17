"""
This module contains all the Brawler data. Each Brawler has a
separate class, which extends from the base (Brawler). Perhaps
subclassing them as `Shotgunners`, `Spawners`, etc would be better.
"""


import random

import discord

from .emojis import emojis, sp_icons, brawler_emojis, rank_emojis


# credits to Star List, developed by Henry
brawler_url = "https://www.starlist.pro/brawlers/detail/{}"
brawler_thumb = "https://www.starlist.pro/assets/brawler/{}.png"


rarity_colors = {
    "Trophy Road": 0x6db2ba,
    "Rare": 0x00d635,
    "Super Rare": 0x0060ac,
    "Epic": 0xa80564,
    "Mythic": 0xe20000,
    "Legendary": 0xf2da02
}


class Brawler:
    """Class to represent a Brawler."""

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

    def _health(self, level) -> int:
        """Function to get health of Brawler of specified power level."""
        stats = self.buff_stats(level)

        return stats['health']
    
    def _attack(self, level):
        """Represent the attack ability of the Brawler. """
        pass
        
    def _ult(self, level):
        """Represent the Super ability of the Brawler."""
        pass

    def _sp1(self):
        """Function to represent the first SP of the Brawler."""
        pass

    def _sp2(self):
        """Function to represent the second SP of the Brawler."""
        pass

    def _spawn(self, level):
        """Represent the spawned character of the Brawler."""
        return None
    
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

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Display brawler info in a formatted way."""

        brawler_name_url = brawler_name.replace(" ", "-")
        brawler_name_url = brawler_name_url.replace("_", "-")

        url = brawler_url.format(brawler_name_url)

        title = f"{brawler_emojis[brawler_name]} {brawler_name}"
        if not level:
            title += f" [Not unlocked]"
        
        embed = discord.Embed(color=rarity_colors[self.rarity], title=title, 
            description=self.desc, url=url)
        embed.set_thumbnail(url=brawler_thumb.format(brawler_name_url.title()))
        if level:
            embed.add_field(name="POWER", value=f"{emojis['xp']} {level}")
            embed.add_field(name="TROPHIES", value=f"{emojis['trophies']} {trophies}")
            embed.add_field(name="PERSONAL BEST", value=f"{rank_emojis['br'+str(rank)]} {pb} [Rank {rank}]")
            if pp > 0:
                embed.add_field(name="POWER POINTS", value=f"{emojis['powerpoint']} {pp}/{next_level_pp}")
            else:
                embed.add_field(name="POWER POINTS", value=f"{emojis['powerpoint']} Maxed")
        else:
            embed.add_field(name="POWER", value=f"{emojis['xp']} 1")
        return embed


class Shelly(Brawler):
    """A class to represent Shelly."""
    
    def _attack(self, level):
        """Represent the attack ability of Shelly."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Shelly."""

        # getting all values 
        ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.8 

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per shell: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per shell: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Nita(Brawler):
    """A class to represent Nita."""

    def _attack(self, level):
        """Represent the attack ability of Nita. """
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Nita."""

        # getting all values
        bear = self.ult["bear"]
        br_range = bear["range"]
        speed = bear["speed"]
        
        stats = self.buff_stats(level)

        damage = stats["bear_damage"]
        health = stats["bear_health"]

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            raw *= 1
        elif chance >= 6:
            raw *= 0.7
        elif chance >= 4:
            raw *= 0.5
        elif chance >= 2:
            raw *= 0.3
        else:
            raw = 0       
        
        return raw, health

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "bear_damage": self.ult["bear"]["damage"],
            "bear_health": self.ult["bear"]["health"]
        }

        return super().buff_stats(stats, level)
    
    def _spawn(self, level):
        a_none_type_object = super()._spawn(level)

        stats = self.buff_stats(level)

        damage = stats["bear_damage"]

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            raw *= 1
        elif chance >= 6:
            raw *= 0.7
        elif chance >= 4:
            raw *= 0.5
        elif chance >= 2:
            raw *= 0.3
        else:
            raw = 0

        return raw

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + (f"\n{emojis['super']} Bear Damage: {stats['bear_damage']}"
                    f"\n{emojis['superhealth']} Bear Health: {stats['bear_health']}")
                    
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Colt(Brawler):
    """A class to represent Colt."""

    def _attack(self, level):
        """Represent the attack ability of Colt."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Colt."""

        # getting all values 
        ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per bullet: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per bullet: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Bull(Brawler):
    """A class to represent Bull."""
    
    def _attack(self, level):
        """Represent the attack ability of Bull."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Bull."""

        # getting all values 
        ult_range = self.ult["range"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per shell: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Jessie(Brawler):
    """A class to represent Jessie."""

    def _attack(self, level):
        """Represent the attack ability of Jessie. """
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Jessie."""

        # getting all values
        scrappy = self.ult["scrappy"]
        br_range = scrappy["range"]
        speed = scrappy["speed"]
        
        stats = self.buff_stats(level)

        damage = stats["scrappy_damage"]
        health = stats["scrappy_health"]

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            raw *= 1
        elif chance >= 6:
            raw *= 0.7
        elif chance >= 4:
            raw *= 0.5
        elif chance >= 2:
            raw *= 0.3
        else:
            raw = 0       
        
        return raw, health

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "scrappy_damage": self.ult["scrappy"]["damage"],
            "scrappy_health": self.ult["scrappy"]["health"]
        }

        return super().buff_stats(stats, level)
    
    def _spawn(self, level):
        a_none_type_object = super()._spawn(level)

        stats = self.buff_stats(level)

        damage = stats["scrappy_damage"]

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            raw *= 1
        elif chance >= 6:
            raw *= 0.7
        elif chance >= 4:
            raw *= 0.5
        elif chance >= 2:
            raw *= 0.3
        else:
            raw = 0

        return raw

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + (f"\n{emojis['super']} Scrappy Damage: {stats['scrappy_damage']}"
                    f"\n{emojis['superhealth']} Scrappy Health: {stats['scrappy_health']}")
                    
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Brock(Brawler):
    """A class to represent Brock."""

    def _attack(self, level):
        """Represent the attack ability of Brock."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Brock."""

        # getting all values 
        ult_range = self.ult["range"]
        _projectiles = self.ult["projectiles"]
        # can deal too much damage otherwise 
        projectiles = random.randint(1, _projectiles)

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per rocket: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Dynamike(Brawler):
    """A class to represent Dynamike."""

    def _attack(self, level):
        """Represent the attack ability of Dynamike."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Dynamike."""

        # getting all values 
        ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per dynamite: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class ElPrimo(Brawler):
    """A class to represent El Primo."""
    
    def _attack(self, level):
        """Represent the attack ability of El Primo."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of El Primo."""

        # getting all values 
        ult_range = self.ult["range"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per punch: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Barley(Brawler):
    """A class to represent Barley."""

    def _attack(self, level):
        """Represent the attack ability of Barley."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        # Barley special -- damage over time
        duration = 0.3

        stats = self.buff_stats(level)

        damage = stats['att_damage']
        # damage over time 
        damage += damage * duration

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Barley."""

        # getting all values 
        ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        # Barley special -- damage over time
        duration = 0.3

        stats = self.buff_stats(level)

        damage = stats['ult_damage']
        # damage over time
        damage += damage * duration

        raw = damage * projectiles * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per second: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per second: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Poco(Brawler):
    """A class to represent Poco."""
    
    def _attack(self, level):
        """Represent the attack ability of Poco."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Poco."""

        # getting all values 
        ult_range = self.ult["range"]

        stats = self.buff_stats(level)

        heal = stats['heal']

        raw = heal * 0.8

        chance = random.randint(0, 10)

        # return raw as a list for healing 
        if chance >= 9:
            return [raw], None
        elif chance >= 6:
            return [raw * 0.7], None
        elif chance >= 4:
            return [raw * 0.5], None
        elif chance >= 2:
            return [raw * 0.3], None
        else:
            return [0], None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "heal": self.ult["heal"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['health']} Heal: {stats['heal']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Rico(Brawler):
    """A class to represent Rico."""

    def _attack(self, level):
        """Represent the attack ability of Rico."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Rico."""

        # getting all values 
        ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
        self, 
        brawler_name: str, 
        trophies: int = None, 
        pb:int = None, 
        rank: int = None,
        level: int = None, 
        pp: int = None, 
        next_level_pp: int = None, 
        sp1=False, 
        sp2=False
    ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per bullet: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per bullet: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Darryl(Brawler):
    """A class to represent Darryl."""
    
    def _attack(self, level):
        """Represent the attack ability of Darryl."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Darryl."""

        # getting all values 
        ult_range = self.ult["range"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage per shell: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Penny(Brawler):
    """A class to represent Penny."""

    def _attack(self, level):
        """Represent the attack ability of Penny."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Penny."""

        # getting all values
        cannon = self.ult["cannon"]
        br_range = cannon["range"]
        
        stats = self.buff_stats(level)

        damage = stats["cannon_damage"]
        health = stats["cannon_health"]

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            raw *= 1
        elif chance >= 6:
            raw *= 0.7
        elif chance >= 4:
            raw *= 0.5
        elif chance >= 2:
            raw *= 0.3
        else:
            raw = 0       
        
        return raw, health

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "cannon_damage": self.ult["cannon"]["damage"],
            "cannon_health": self.ult["cannon"]["health"]
        }

        return super().buff_stats(stats, level)
    
    def _spawn(self, level):
        a_none_type_object = super()._spawn(level)

        stats = self.buff_stats(level)

        damage = stats["cannon_damage"]

        raw = damage * 0.8

        chance = random.randint(0, 10)

        if chance >= 9:
            raw *= 1
        elif chance >= 6:
            raw *= 0.7
        elif chance >= 4:
            raw *= 0.5
        elif chance >= 2:
            raw *= 0.3
        else:
            raw = 0

        return raw

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1
        
        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + (f"\n{emojis['super']} Cannon Damage: {stats['cannon_damage']}"
                    f"\n{emojis['superhealth']} Cannon Health: {stats['cannon_health']}")
                    
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Carl(Brawler):
    """A class to represent Carl."""
    
    def _attack(self, level):
        """Represent the attack ability of Carl."""
        
        # getting all values 
        att_range = self.attack["range"]
        att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

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
        """Represent the Super ability of Carl."""

        # getting all values 
        duration = self.ult["duration"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * 0.8 * duration

        chance = random.randint(0, 10)

        if chance >= 9:
            return raw, None
        elif chance >= 6:
            return raw * 0.7, None
        elif chance >= 4:
            return raw * 0.5, None
        elif chance >= 2:
            return raw * 0.3, None
        else:
            return 0, None

    def buff_stats(self, level: int):
        stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

        return super().buff_stats(stats, level)

    def brawler_info(
            self, 
            brawler_name: str, 
            trophies: int = None, 
            pb:int = None, 
            rank: int = None,
            level: int = None, 
            pp: int = None, 
            next_level_pp: int = None, 
            sp1=False, 
            sp2=False
        ):
        """Return embed with Brawler info."""

        embed = super().brawler_info(brawler_name=brawler_name, trophies=trophies, pb=pb, 
                            rank=rank, level=level, pp=pp, next_level_pp=next_level_pp, sp1=sp1, sp2=sp2)

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_desc = f"> {self.attack['desc']}"
        attack_str = attack_desc + f"\n{emojis['damage']} Damage on hit: {stats['att_damage']}"
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_desc = f"> {self.ult['desc']}"
        super_str = super_desc + f"\n{emojis['super']} Damage per swing: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons[brawler_name][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


brawlers_map = {
    "Shelly": Shelly,
    "Nita": Nita,
    "Colt": Colt,
    "Bull": Bull,
    "Jessie": Jessie,
    "Brock": Brock,
    "Dynamike": Dynamike,
    "El Primo": ElPrimo,
    "Barley": Barley,
    "Poco": Poco,
    "Rico": Rico,
    "Darryl": Darryl,
    "Penny": Penny,
    "Carl": Carl
}
