import random

import discord

from .emojis import brawler_emojis, emojis, rank_emojis, sp_icons


# Credits to Star List, developed by Henry.
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
    """Base class to represent a Brawler."""

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

        self.init()

    def init(self):
        # These are the stats that are "buffed", unless overridden in specific classes.
        self.stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_damage": self.ult["damage"]
        }

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
        """Get the health of the Brawler at specified power level."""

        return self.buff_stat(self.health, level)

    def _attack(self, level):
        """Represents the attack ability of the Brawler."""

        # getting all values
        # att_range = self.attack["range"]
        # att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        raw = damage * projectiles * 0.8

        return self.chance_calculation(raw)

    def _ult(self, level):
        """Represents the Super ability of the Brawler."""

        # getting all values
        # # ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * projectiles * 0.8

        return self.chance_calculation(raw), None  # None is the spawn health

    def _sp1(self):
        """Represents the first SP of the Brawler."""
        pass

    def _sp2(self):
        """Represents the second SP of the Brawler."""
        pass

    def _spawn(self, level):
        """Represents the move of the spawned character of the Brawler."""

    def buff_stats(self, level: int):
        """Get all Brawler stats buffed by specified level."""

        if level == 10:
            level = 9

        stats = {}

        for stat in self.stats:
            val = self.stats[stat]
            if not val:
                continue
            stats[stat] = val + int(val/20 * (level - 1))

        return stats

    def buff_stat(self, stat: int, level: int):
        """Get a single Brawler stat buffed by specified level."""

        if level == 10:
            level = 9

        stat += int(stat/20 * (level - 1))

        return stat

    def brawler_info(
        self,
        brawler_name: str,
        trophies: int = None,
        pb: int = None,
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

        embed = discord.Embed(
            color=rarity_colors[self.rarity], title=title,
            description=self.desc, url=url
        )
        embed.set_thumbnail(url=brawler_thumb.format(brawler_name_url.title()))

        if level:
            embed.add_field(name="POWER", value=f"{emojis['xp']} {level}")
            embed.add_field(
                name="TROPHIES", value=f"{emojis['trophies']} {trophies}"
            )
            embed.add_field(
                name="PERSONAL BEST",
                value=f"{rank_emojis['br'+str(rank)]} {pb} [Rank {rank}]"
            )
            if pp >= 0:
                embed.add_field(
                    name="POWER POINTS",
                    value=f"{emojis['powerpoint']} {pp}/{next_level_pp}"
                )
            else:
                embed.add_field(
                    name="POWER POINTS", value=f"{emojis['powerpoint']} Maxed"
                )
        else:
            embed.add_field(name="POWER", value=f"{emojis['xp']} 1")

        if not level:
            level = 1

        stats = self.buff_stats(level)

        embed.add_field(name="HEALTH", value=f"{emojis['health']} {stats['health']}")
        embed.add_field(name="SPEED", value=f"{emojis['speed']} {self.speed}")

        attack_str = self.attack_info(stats)
        embed.add_field(name="ATTACK", value=attack_str, inline=False)

        super_str = self.super_info(stats)
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"

        sp_str = (
            f"{sp_icons[brawler_name][0]} **{self.sp1['name']}**{u1}"
            f"\n```k\n{self.sp1['desc']}```\n{sp_icons[brawler_name][1]}"
            f" **{self.sp2['name']}**{u2}\n```k\n{self.sp2['desc']}```"
        )

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed

    def attack_info(self, stats: dict):
        try:
            attack_str = self.attack['extra']
        except KeyError:
            attack_str = "Damage"

        attack_desc = f"```{self.attack['desc']}```"
        info = f"{attack_desc}\n{emojis['damage']} {attack_str}: {stats['att_damage']}"

        return info

    def super_info(self, stats: dict):
        try:
            super_str = self.ult['extra']
        except KeyError:
            super_str = "Damage"

        super_desc = f"```{self.ult['desc']}```"
        info = f"{super_desc}\n{emojis['super']} {super_str}: {stats['ult_damage']}"

        return info

    def chance_calculation(self, raw: int):
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


class Healer(Brawler):
    """Class to represent a Brawler that heals using Super."""

    def init(self):
        self.stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "ult_heal": self.ult["heal"]
        }

    def _ult(self, level):
        """Represents the Super ability of Poco."""

        # getting all values
        # ult_range = self.ult["range"]

        stats = self.buff_stats(level)

        heal = stats['heal']

        raw = heal * 0.8

        return [self.chance_calculation(raw)], None

    def super_info(self, stats: dict):
        try:
            super_str = self.ult['extra']
        except KeyError:
            super_str = "Heal"

        super_desc = f"```{self.ult['desc']}```"
        info = f"{super_desc}\n{emojis['superhealth']} {super_str}: {stats['ult_heal']}"

        return info


class Spawner(Brawler):
    """Class to represent a Brawler that spawns a character."""

    def init(self):
        self.stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "spawn_damage": self.ult["spawn"]["damage"],
            "spawn_health": self.ult["spawn"]["health"]
        }

    def _ult(self, level):
        """Represents the Super ability of Nita."""

        # getting all values

        stats = self.buff_stats(level)

        damage = stats["spawn_damage"]
        health = stats["spawn_health"]

        raw = damage * 0.8

        return self.chance_calculation(raw), health

    def _spawn(self, level):
        """Represents the move of the spawned character of the Brawler."""

        stats = self.buff_stats(level)

        damage = stats["spawn_damage"]

        raw = damage * 0.8

        return self.chance_calculation(raw)

    def super_info(self, stats):
        try:
            super_str = self.ult['extra']
        except KeyError:
            super_str = "Damage"

        super_desc = f"```{self.ult['desc']}```"

        info = (
            "{desc}\n{att_emote} {spawn} {extra}: {damage}"
            "\n{health_emote} {spawn} Health: {health}"
        ).format(
            desc=super_desc,
            att_emote=emojis['super'],
            spawn=self.ult['spawn']['name'],
            extra=super_str,
            damage=stats['spawn_damage'],
            health_emote=emojis['superhealth'],
            health=stats['spawn_health']
        )

        return info


class HealSpawner(Brawler):
    """Class to represent Brawlers whose spanws heal.

    This exists as a separate class because of the additional "spawn_heal" element.
    """

    def init(self):
        self.stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "spawn_heal": self.ult["spawn"]["heal"],
            "spawn_health": self.ult["spawn"]["health"]
        }

    def _ult(self, level):
        """Represents the Super ability of Nita."""

        # getting all values

        stats = self.buff_stats(level)

        heal = stats["spawn_heal"]
        health = stats["spawn_health"]

        raw = heal * 0.8

        return self.chance_calculation(raw), health

    def _spawn(self, level):
        """Represents the move of the spawned character of Pam."""

        heal = self.buff_stat(self.ult["spawn"]["heal"], level)

        raw = heal * 0.8

        return [self.chance_calculation(raw)]

    def super_info(self, stats):
        try:
            super_str = self.ult['extra']
        except KeyError:
            super_str = "Heal"

        super_desc = f"```{self.ult['desc']}```"

        info = (
            "{desc}\n{att_emote} {spawn} {extra}: {damage}"
            "\n{health_emote} {spawn} Health: {health}"
        ).format(
            desc=super_desc,
            att_emote=emojis['super'],
            spawn=self.ult['spawn']['name'],
            extra=super_str,
            damage=stats['spawn_heal'],
            health_emote=emojis['superhealth'],
            health=stats['spawn_health']
        )

        return info


# SPECIAL BRAWLER CLASSES
# These override at least one base method. They also inherit from the base `Brawler` class.

# Overrides `_ult` method to factor in damage over time.
class Barley(Brawler):
    """Class to represent Barley."""

    def _ult(self, level):
        """Represent the Super ability of Barley."""

        # getting all values
        # ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        # Barley special -- damage over time
        duration = 0.3

        stats = self.buff_stats(level)

        damage = stats['ult_damage']
        # Damage over time
        damage += damage * duration

        raw = damage * projectiles * 0.8

        return self.chance_calculation(raw), None


# Overrides `_ult` method to factor in spin duration.
class Carl(Brawler):
    """Class to represent Carl."""

    def _ult(self, level):
        """Represent the Super ability of Carl."""

        # getting all values
        duration = self.ult["duration"]

        stats = self.buff_stats(level)

        damage = stats['ult_damage']

        raw = damage * 0.8 * duration

        return self.chance_calculation(raw), None


# Overrides `_attack` method to factor in range scaling.
class Piper(Brawler):
    """Class to represent Piper."""

    def _attack(self, level):
        """Represents the attack ability of Piper."""

        # getting all values
        range_ = self.attack["range"]
        # att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = stats['att_damage']

        range_scaling = random.randint(range_ - 4, range_) * 0.1

        raw = damage * projectiles * 0.8 * range_scaling

        return self.chance_calculation(raw)


# Overrides `init`, `_attack`, `_ult` and `attack_info` methods to factor in poison damage.
class Crow(Brawler):
    """Class to represent Crow."""

    def init(self):
        self.stats = {
            "health": self.health,
            "att_damage": self.attack["damage"],
            "poison_damage": self.attack["poison_damage"],
            "ult_damage": self.ult["damage"]
        }

    def _attack(self, level):
        """Represents the attack ability of Crow."""

        # getting all values
        # att_range = self.attack["range"]
        # att_reload = self.attack["reload"]
        projectiles = self.attack["projectiles"]

        stats = self.buff_stats(level)

        damage = (
            stats['att_damage']
            + stats['poison_damage'] * random.randint(1, 3)
        )

        raw = damage * projectiles * 0.8

        return self.chance_calculation(raw)

    def _ult(self, level):
        """Represents the Super ability of Crow."""

        # getting all values
        # ult_range = self.ult["range"]
        projectiles = self.ult["projectiles"]

        stats = self.buff_stats(level)

        damage = (
            stats['ult_damage']
            + stats['poison_damage'] * random.randint(1, 3)
        )

        raw = damage * projectiles * 0.8

        return self.chance_calculation(raw), None

    def attack_info(self, stats):
        try:
            attack_str = self.attack['extra']
        except KeyError:
            attack_str = "Damage"

        attack_desc = f"```{self.attack['desc']}```"

        info = (
            "{desc}\n{att_emote} {extra}: {damage} \n{att_emote} Poison damage: {poison}"
        ).format(
            desc=attack_desc,
            att_emote=emojis['damage'],
            extra=attack_str,
            damage=stats['att_damage'],
            poison=stats['poison_damage']
        )

        return info


# GENERAL BRAWLER CLASSES
# These exist just for the sake of having a class for each Brawler.
# They simply inherit from appropriate base classes
# (`Brawler`, `Healer`, `Spawner` or `HealSpawner`).

class Shelly(Brawler):
    """Class to represent Shelly."""


class Nita(Spawner):
    """Class to represent Nita."""


class Colt(Brawler):
    """Class to represent Colt."""


class Bull(Brawler):
    """Class to represent Bull."""


class Jessie(Spawner):
    """Class to represent Jessie."""


class Brock(Brawler):
    """Class to represent Brock."""


class Dynamike(Brawler):
    """Class to represent Dynamike."""


class ElPrimo(Brawler):
    """Class to represent El Primo."""


class Poco(Healer):
    """Class to represent Poco."""


class Rico(Brawler):
    """Class to represent Rico."""


class Darryl(Brawler):
    """Class to represent Darryl."""


class Penny(Spawner):
    """Class to represent Penny."""


class Bo(Brawler):
    """Class to represent Bo."""


class Pam(HealSpawner):
    """Class to represent Pam."""


class Mortis(Brawler):
    """Class to represent Mortis."""


class Frank(Brawler):
    """Class to represent Frank."""


class Tara(Brawler):
    """Class to represent Tara."""


class Spike(Brawler):
    """Class to represent Spike."""


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
    "Carl": Carl,
    "Bo": Bo,
    "Piper": Piper,
    "Pam": Pam,
    "Mortis": Mortis,
    "Frank": Frank,
    "Tara": Tara,
    "Spike": Spike,
    "Crow": Crow
}
