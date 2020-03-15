import random

import discord
from redbot.core import commands
from redbot.core.commands import Context

from .brawlhelp import EMBED_COLOR
from .emojis import brawler_emojis, emojis, sp_icons
from .errors import MaintenanceError

default_stats = {
    "trophies": 0,
    "pb": 0,
    "rank": 1,
    "level": 1,
    "powerpoints": 0,
    "total_powerpoints": 0,
    "skins": ["Default"],
    "selected_skin": "Default",
    "sp1": False,
    "sp2": False
}


class Box:
    """A class to represent Boxes."""

    def __init__(self, all_brawlers, brawler_data):
        # variables to store possibilities data
        self.can_unlock = {
            "Rare": [],
            "Super Rare": [],
            "Epic": [],
            "Mythic": [],
            "Legendary": []
        }
        self.can_get_pp = {}
        self.can_get_sp = {}

        # odds
        self.powerpoint = 94.6516
        self.rare = 2.2103
        self.superrare = 1.2218
        self.epic = 0.5527
        self.mythic = 0.2521
        self.legendary = 0.1115
        self.starpower = 1

        self.tickets = 25
        self.gems = 9
        self.td = 3  # token doubler

        # number of powerpoints required to max
        self.max_pp = 1410

        self.pop = [
            "Power Points", "Rare", "Super Rare",
            "Epic", "Mythic", "Legendary", "Star Power"
        ]
        self.weights = [
            self.powerpoint,
            self.rare,
            self.superrare,
            self.epic,
            self.mythic,
            self.legendary,
            self.starpower
        ]

        self.BRAWLERS = all_brawlers

        for brawler in all_brawlers:
            rarity = all_brawlers[brawler]["rarity"]
            if rarity != "Trophy Road":
                if brawler not in brawler_data:
                    self.can_unlock[rarity].append(brawler)

        for brawler in brawler_data:
            # self.owned.append(brawler)
            total_powerpoints = brawler_data[brawler]['total_powerpoints']
            if total_powerpoints < self.max_pp:
                self.can_get_pp[brawler] = self.max_pp - total_powerpoints

            level = brawler_data[brawler]['level']
            if level >= 9:
                sp1 = brawler_data[brawler]['sp1']
                sp2 = brawler_data[brawler]['sp2']

                if sp1 is False and sp2 is True:
                    self.can_get_sp[brawler] = ['sp1']
                elif sp1 is True and sp2 is False:
                    self.can_get_sp[brawler] = ['sp2']
                elif sp1 is False and sp2 is False:
                    self.can_get_sp[brawler] = ['sp1', 'sp2']
                else:
                    pass

    def weighted_random(self, lower, upper, avg):
        avg_low = (avg + lower) / 2
        avg_high = (upper + avg) / 2

        p_high = (avg - avg_low) / (avg_high - avg_low)

        chance = random.random()

        if chance < p_high:
            return random.randint(avg, upper)
        else:
            return random.randint(lower, avg)

    def split_in_integers(self, N, m, base=1):
        """Returns a list after splitting a number into number of integers (m)

        Number of integers to split in should be less than the base.
        """

        assert m * base <= N
        breaks = ([-1] + sorted(
            random.sample(range(N - m * base + m - 1), m - 1)
        ) + [N - m * base + m - 1])
        buckets = [base] * m
        for idx in range(m):
            buckets[idx] += (breaks[idx + 1] - breaks[idx] - 1)
        return buckets

    async def brawlbox(self, conf, user):
        """Function to handle brawl box openings."""

        gold = self.weighted_random(12, 70, 19)

        rarities = []
        starpowers = 0
        stacks = 0

        selected = random.choices(
            population=self.pop, weights=self.weights, k=2
        )

        for i in selected:
            if i == "Power Points":
                stacks += 1
            elif i == "Star Power":
                starpowers += 1
            else:
                rarities.append(i)

        if len(self.can_get_pp) == 0:
            gold *= 3
            stacks = 0

        elif len(self.can_get_pp) == 1:
            gold *= 2
            stacks = 1

        if stacks > 0:
            powerpoints = int(self.weighted_random(7, 25, 14))

            pieces = self.split_in_integers(powerpoints, stacks)

            pp_str = ""

            if pieces:
                for piece in pieces:
                    items = list(self.can_get_pp.items())
                    random.shuffle(items)
                    for brawler, threshold in items:
                        if piece <= threshold:
                            async with conf.brawlers() as brawlers:
                                brawlers[brawler]['powerpoints'] += piece
                                brawlers[brawler]['total_powerpoints'] += piece
                                pp_str += (
                                    f"\n{brawler_emojis[brawler]} **{brawler}:"
                                    f"** {emojis['powerpoint']} {piece}"
                                )
                        else:
                            continue
                        break

        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)

        embed = discord.Embed(
            color=EMBED_COLOR,
            title=f"{emojis['brawlbox']} Brawl Box"
        )
        # embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(
            name="Gold", value=f"{emojis['gold']} {gold}", inline=False)

        if stacks > 0:
            if pp_str:
                embed.add_field(
                    name="Power Points", value=pp_str.strip(), inline=False)

        if rarities:
            for rarity in rarities:
                rarity = self.check_rarity(rarity)
                if rarity:
                    embed = await self.unlock_brawler(rarity, conf, embed)
                else:
                    self.tickets *= 2
                    self.gems *= 2
                    self.td *= 2

        # star power
        for _ in range(starpowers):
            if self.can_get_sp:
                embed = await self.get_starpower(conf, embed)
            else:
                self.tickets *= 2
                self.gems *= 2
                self.td *= 2

        chance = random.randint(1, 100)

        if chance <= self.td:
            old_td = await conf.token_doubler()
            await conf.token_doubler.set(200 + old_td)
            embed.add_field(
                name="Token Doubler", value=f"{emojis['tokendoubler']} 200"
            )
        elif chance <= self.gems:
            try:
                old_gems = await conf.gems()
            except Exception:
                old_gems = 0
            gems = random.randint(2, 5)
            await conf.gems.set(gems + old_gems)
            embed.add_field(name="Gems", value=f"{emojis['gem']} {gems}")
        elif chance <= self.tickets:
            old_tickets = await conf.tickets()
            await conf.tickets.set(1 + old_tickets)
            embed.add_field(name="Tickets", value=f"{emojis['ticket']} 1")

        return embed

    async def bigbox(self, conf, user):
        """Function to handle brawl box openings."""

        gold = self.weighted_random(36, 210, 63)

        rarities = []
        starpowers = 0
        stacks = 0

        selected = random.choices(
            population=self.pop, weights=self.weights, k=5
        )

        for i in selected:
            if i == "Power Points":
                stacks += 1
            elif i == "Star Power":
                starpowers += 1
            else:
                rarities.append(i)

        if len(self.can_get_pp) == 0:
            gold *= 3
            stacks = 0
        elif len(self.can_get_pp) == 1:
            gold *= 2
            stacks = 1
        elif len(self.can_get_pp) < stacks:
            stacks = len(self.can_get_pp)
            self.tickets *= 1.5
            self.gems *= 1.5
            self.td *= 1.5

        if stacks > 0:
            powerpoints = int(self.weighted_random(27, 75, 46))

            pieces = self.split_in_integers(powerpoints, stacks)

            pp_str = ""

            if pieces:
                for piece in pieces:
                    items = list(self.can_get_pp.items())
                    random.shuffle(items)
                    for brawler, threshold in items:
                        if piece <= threshold:
                            async with conf.brawlers() as brawlers:
                                brawlers[brawler]['powerpoints'] += piece
                                brawlers[brawler]['total_powerpoints'] += piece
                                pp_str += (
                                    f"\n{brawler_emojis[brawler]} **{brawler}:"
                                    f"** {emojis['powerpoint']} {piece}"
                                )
                        else:
                            continue
                        break

        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)

        embed = discord.Embed(
            color=EMBED_COLOR,
            title=f" {emojis['bigbox']} Big Box"
        )
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(
            name="Gold", value=f"{emojis['gold']} {gold}", inline=False
        )

        if stacks > 0:
            if pp_str:
                embed.add_field(
                    name="Power Points", value=pp_str.strip(), inline=False
                )

        if rarities:
            for rarity in rarities:
                rarity = self.check_rarity(rarity)
                if rarity:
                    embed = await self.unlock_brawler(rarity, conf, embed)
                else:
                    self.tickets *= 2
                    self.gems *= 2
                    self.td *= 2

        # star power
        for _ in range(starpowers):
            if self.can_get_sp:
                embed = await self.get_starpower(conf, embed)
            else:
                self.tickets *= 2
                self.gems *= 2
                self.td *= 2

        chance = random.randint(1, 100)

        if chance <= self.td:
            old_td = await conf.token_doubler()
            await conf.token_doubler.set(200 + old_td)
            embed.add_field(
                name="Token Doubler", value=f"{emojis['tokendoubler']} 200"
            )
        elif chance <= self.gems:
            try:
                old_gems = await conf.gems()
            except Exception:
                old_gems = 0
            gems = random.randint(6, 15)
            await conf.gems.set(gems + old_gems)
            embed.add_field(name="Gems", value=f"{emojis['gem']} {gems}")
        elif chance <= self.tickets:
            old_tickets = await conf.tickets()
            await conf.tickets.set(4 + old_tickets)
            embed.add_field(name="Tickets", value=f"{emojis['ticket']} 4")

        return embed

    async def megabox(self, conf, user):
        """Function to handle mega box openings."""

        gold = self.weighted_random(36, 210, 63)

        rarities = []
        starpowers = 0
        stacks = 0

        selected = random.choices(
            population=self.pop, weights=self.weights, k=9
        )

        for i in selected:
            if i == "Power Points":
                stacks += 1
            elif i == "Star Power":
                starpowers += 1
            else:
                rarities.append(i)

        if len(self.can_get_pp) == 0:
            gold *= 3
            stacks = 0
        elif len(self.can_get_pp) == 1:
            gold *= 2
            stacks = 1
        elif len(self.can_get_pp) < stacks:
            stacks = len(self.can_get_pp)
            self.tickets *= 2
            self.gems *= 2
            self.td *= 2

        if stacks > 0:
            powerpoints = int(self.weighted_random(81, 225, 132))

            pieces = self.split_in_integers(powerpoints, stacks)
            pp_str = ""

            if pieces:
                for piece in pieces:
                    items = list(self.can_get_pp.items())
                    random.shuffle(items)
                    for brawler, threshold in items:
                        if piece <= threshold:
                            async with conf.brawlers() as brawlers:
                                brawlers[brawler]['powerpoints'] += piece
                                brawlers[brawler]['total_powerpoints'] += piece
                                pp_str += (
                                    f"\n{brawler_emojis[brawler]} **{brawler}:"
                                    f"** {emojis['powerpoint']} {piece}"
                                )
                        else:
                            continue
                        break

        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)

        embed = discord.Embed(
            color=EMBED_COLOR, title=f" {emojis['megabox']} Mega Box"
        )
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(
            name="Gold", value=f"{emojis['gold']} {gold}", inline=False)

        if stacks > 0:
            if pp_str:
                embed.add_field(
                    name="Power Points", value=pp_str.strip(), inline=False)

        if rarities:
            for rarity in rarities:
                rarity = self.check_rarity(rarity)
                if rarity:
                    embed = await self.unlock_brawler(rarity, conf, embed)
                else:
                    self.tickets *= 2
                    self.gems *= 2
                    self.td *= 2

        # star power
        for _ in range(starpowers):
            if self.can_get_sp:
                embed = await self.get_starpower(conf, embed)
            else:
                self.tickets *= 2
                self.gems *= 2
                self.td *= 2

        chance = random.randint(1, 100)

        if chance <= self.td:
            old_td = await conf.token_doubler()
            await conf.token_doubler.set(200 + old_td)
            embed.add_field(
                name="Token Doubler", value=f"{emojis['tokendoubler']} 200"
            )
        elif chance <= self.gems:
            try:
                old_gems = await conf.gems()
            except Exception:
                old_gems = 0
            gems = random.randint(18, 45)
            await conf.gems.set(gems + old_gems)
            embed.add_field(name="Gems", value=f"{emojis['gem']} {gems}")
        elif chance <= self.tickets:
            old_tickets = await conf.tickets()
            await conf.tickets.set(12 + old_tickets)
            embed.add_field(name="Tickets", value=f"{emojis['ticket']} 12")

        return embed

    async def unlock_brawler(self, rarity, conf, embed):
        brawler = random.choice(self.can_unlock[rarity])
        free_skins = [
            skin for skin in self.BRAWLERS[brawler]["skins"] if skin[0] == 0
        ]
        async with conf.brawlers() as brawlers:
            default_stats["skins"].append(free_skins)
            brawlers[brawler] = default_stats
        embed.add_field(
            name=f"New {rarity} Brawler :tada:",
            value=f"{brawler_emojis[brawler]} {brawler}",
            inline=False
        )

        return embed

    def check_rarity(self, rarity):
        """Return rarity by checking the rarities from which user can unlock a brawler.

        ``False`` is returned if no rarity brawler can be unlocked.
        """

        def lower_rarity(rarity):
            if rarity == "Legendary":
                return "Mythic"
            elif rarity == "Mythic":
                return "Epic"
            elif rarity == "Epic":
                return "Super Rare"
            elif rarity == "Super Rare":
                return "Rare"
            else:
                return False

        while True:
            if not rarity:
                break
            if not self.can_unlock[rarity]:
                rarity = lower_rarity(rarity)
            else:
                break

        return rarity

    async def get_starpower(self, conf, embed):
        sp_brawler = random.choice(list(self.can_get_sp.keys()))
        sp = random.choice(self.can_get_sp[sp_brawler])

        self.can_get_sp[sp_brawler].remove(sp)

        sp_name = self.BRAWLERS[sp_brawler][sp]["name"]
        sp_desc = self.BRAWLERS[sp_brawler][sp]["desc"]
        sp_index = int(sp[2]) - 1

        sp_str = (
            f"{sp_icons[sp_brawler][sp_index]} {sp_name}"
            f" - {brawler_emojis[sp_brawler]}"
            f" {sp_brawler}\n> {sp_desc}"
        )

        async with conf.brawlers() as brawlers:
            brawlers[sp_brawler]["level"] = 10
            brawlers[sp_brawler][sp] = True

        embed.add_field(
            name="New Star Power :tada:", value=sp_str, inline=False
        )

        return embed


def maintenance():
    """A decorator which checks for maintenance."""

    async def predicate(ctx: Context):
        if await ctx.bot.is_owner(ctx.author):
            # True means command should run
            return True

        cog = ctx.cog
        if cog:
            config = cog.config

            async with config.maintenance() as maint:
                setting = maint["setting"]

                if setting:
                    raise MaintenanceError(
                        "The bot is currently under maintenance. It will end"
                        f" in approx. {maint['duration']} minutes."
                        " Commands will not work till then."
                        " Sorry for the inconvenience!"
                    )
        # Run command if not maintenance
        return True

    return commands.check(predicate)
