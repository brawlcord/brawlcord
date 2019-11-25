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
    "xp": "<:xp:645337312431046657>",
    "token": "<:token:645694990302838789>",
    "gold": "<:gold:645337311923404851>",
    "starpoints": "<:starpoint:646249196042715138>",
    "brawlbox": "<:brawlbox:646307503650373632>",
    "bigbox": "<:bigbox:646307503524544518>",
    "megabox": "<:megabox:646307503835054080>",
    "ticket": "<:bsticket:645337313131495434>",
    "tokendoubler": "<:token_doubler:646308736130088961>",
    "bsstar": "<:bs_icon_ready:646310961241653253>",
    "superhealth": "<:super_health:646723200436404285>",
    "gem": "<:bsgem:645337311852232714>",
    "spblank": "<:sp_blank:647382632006680606>",
    "spgrey": "<:sp_greyed_out:647382542109900804>",
    "startoken": "<:startoken:645694989417840670>",
    "wintrophy": "<:fwin_trophy:648085703795933194>",
    "powerplay": "<:powerplay:645341012646035459>"
}

sp_icons = {
    "Shelly": ["<:ShellShock:645349547127603246>", "<:BandAid:645349544837644322>"],
    "Nita": ["<:BearWithMe:645349544304967753>", "<:HyperBear:645349548411191336>"],
    "Colt": ["<:SlickBoots:645349548386025503>", "<:MagnumSpecial:647170353738547259>"],
    "Bull": ["<:Berserker:645349545181708300>", "<:ToughGuy:647170354044731392>"],
    "Jessie": ["<:Energize:645349548121653279>", "<:Shocky:647170352962600993>"]
}

rarity_colors = {
    "Trophy Road": 0x6db2ba,
    "Rare": 0x00d635,
    "Super Rare": 0x0060ac,
    "Epic": 0xa80564,
    "Mythic": 0xe20000,
    "Legendary": 0xf2da02
}

brawler_emojis = {
    "Barley": "<:Barley:645584757903589377>",
    "Bull": "<:Bull:645584757949988874>",
    "Bo": "<:Bo:645584758046195742>",
    "Brock": "<:Brock:645584758163767296>",
    "8Bit": "<:8Bit:645584758364962816>",
    "Bibi": "<:Bibi:645584758700507137>",
    "Colt": "<:Colt:645584759141171212>",
    "Spike": "<:Spike:645584759262674976>",
    "Carl": "<:Carl:645584759422189578>",
    "Crow": "<:Crow:645584759459807242>",
    "Jessie": "<:Jessie:645584759501881355>",
    "Gene": "<:Gene:645584759761666048>",
    "Tick": "<:Tick:645584759829037067>",
    "El Primo": "<:ElPrimo:645589193900425236>",
    "Rosa": "<:Rosa:645584760168644609>",
    "Dynamike": "<:Dynamike:645584760185552897>",
    "Tara": "<:Tara:645584760260919296>",
    "Darryl": "<:Darryl:645584760395005973>",
    "Frank": "<:Frank:645584760424497153>",
    "Pam": "<:Pam:645584760487411744>",
    "Leon": "<:Leon:645584760550457346>",
    "Nita": "<:Nita:645584760911167488>",
    "Poco": "<:Poco:645584760915230740>",
    "Emz": "<:Emz:645584760923750430>",
    "Mortis": "<:Mortis:645584760952848404>",
    "Sandy": "<:Sandy:645584761191923712>",
    "Shelly": "<:Shelly:645584761200574464>",
    "Rico": "<:Rico:645584761204506634>",
    "Penny": "<:Penny:645584761208700948>",
    "Piper": "<:Piper:645584761250775050>",
}

# image_urls = {
#     "powerpoint": "https://cdn.discordapp.com/emojis/645333239103488029.png?v=1"
# }

rank_emojis = {
    "br2": "<:br2:646238169276088322>",
    "br7": "<:br7:646238169410568194>",
    "br1": "<:br1:646238169506906123>",
    "br5": "<:br5:646238169720815616>",
    "br3": "<:br3:646238169754501130>",
    "br8_": "<:br8_:646238169821609985>",
    "br10": "<:br10:646238169909428249>",
    "br16": "<:br16:646238170001833985>",
    "br4": "<:br4:646238170027130880>",
    "br9": "<:br9:646238170043908109>",
    "br14": "<:br14:646238170081525760>",
    "br24": "<:br24:646238170140377091>",
    "br12": "<:br12:646238170148634634>",
    "br6": "<:br6:646238170211418142>",
    "br18": "<:br18:646238170257817600>",
    "br11": "<:br11:646238170262011914>",
    "br15": "<:br15:646238170379452427>",
    "br20": "<:br20:646238170437910537>",
    "br13": "<:br13:646238170442235905>",
    "br19": "<:br19:646238170442366986>",
    "br34": "<:br34:646238170450624512>",
    "br28": "<:br28:646238170517864448>",
    "br32": "<:br32:646238170521927680>",
    "br17": "<:br17:646238170526121984>",
    "br21": "<:br21:646238170530185217>",
    "br29": "<:br29:646238170564001797>",
    "br33": "<:br33:646238170593361920>",
    "br35": "<:br35:646238170610008064>",
    "br31": "<:br31:646238170689830912>",
    "br22": "<:br22:646238170719059968>",
    "br27": "<:br27:646238170735706112>",
    "br26": "<:br26:646238170807009280>",
    "br25": "<:br25:646238171058667521>",
    "br23": "<:br23:646238171469709323>",
    "br30": "<:br30:646238171474165760>",
}

# average_range = 7.23


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

        brawler_name = brawler_name.replace(" ", "-")
        brawler_name = brawler_name.replace("_", "-")

        url = brawler_url.format(brawler_name)

        title = f"{brawler_emojis[brawler_name]} {brawler_name}"
        if not level:
            title += f" [Not unlocked]"
        
        embed = discord.Embed(color=rarity_colors[self.rarity], title=title, 
            description=self.desc, url=url)
        embed.set_thumbnail(url=brawler_thumb.format(brawler_name.title()))
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
        damage = self.ult["damage"]
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
        
        sp_str = (f"{sp_icons['Shelly'][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons['Shelly'][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

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
        
        sp_str = (f"{sp_icons['Nita'][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons['Nita'][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed


class Colt(Brawler):
    """A class to represent Colt."""

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
        damage = self.ult["damage"]
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
        
        sp_str = (f"{sp_icons['Colt'][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons['Colt'][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

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
        damage = self.ult["damage"]
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
        super_str = super_desc + f"\n{emojis['super']} Damage per shell: {stats['ult_damage']}"
        embed.add_field(name="SUPER", value=super_str, inline=False)

        u1 = u2 = ""

        if sp1:
            u1 = " [Owned]"
        if sp2:
            u2 = " [Owned]"
        
        sp_str = (f"{sp_icons['Bull'][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons['Bull'][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

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
        
        sp_str = (f"{sp_icons['Jessie'][0]} **{self.sp1['name']}**{u1}\n> {self.sp1['desc']}"
                            f"\n{sp_icons['Jessie'][1]} **{self.sp2['name']}**{u2}\n> {self.sp2['desc']}")

        embed.add_field(name="STAR POWERS", value=sp_str, inline=False)

        return embed
