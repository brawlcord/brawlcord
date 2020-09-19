import random
from datetime import datetime

import discord
from redbot.core import Config
from redbot.core.commands import Context
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from .box import Box
from .emojis import emojis, brawler_emojis, sp_icons

EMBED_COLOR = 0x74FFBE


class Shop:
    """Class for representing daily shop."""

    def __init__(self, all_brawlers=None, brawlers_data=None):
        self.max_slots = 6
        self.max_skins = (4, 2)  # 4 gem and 2 starpoint skins
        self.shop_items = {}

        # items with tuple structured as (gold cost, odds)
        self.items = {
            "powerpoints": (2, 100),
            "starpowers": (2000, 10),
            "brawlbox": (0, 20),
            "tickets": (0, 10)
        }

        # number of powerpoints required to max
        self.max_pp = 1410

        self.ALL_BRAWLERS = all_brawlers
        self.BRAWLERS_DATA = brawlers_data

        self.can_get_pp = {}
        self.can_get_sp = {}

        if brawlers_data:
            for brawler in brawlers_data:
                if brawler not in all_brawlers:
                    continue

                total_powerpoints = brawlers_data[brawler]['total_powerpoints']
                if total_powerpoints < self.max_pp:
                    self.can_get_pp[brawler] = self.max_pp - total_powerpoints

                level = brawlers_data[brawler]['level']
                if level >= 9:
                    sp1 = brawlers_data[brawler]['sp1']
                    sp2 = brawlers_data[brawler]['sp2']

                    if sp1 is False and sp2 is True:
                        self.can_get_sp[brawler] = ['sp1']
                    elif sp1 is True and sp2 is False:
                        self.can_get_sp[brawler] = ['sp2']
                    elif sp1 is False and sp2 is False:
                        self.can_get_sp[brawler] = ['sp1', 'sp2']
                    else:
                        pass

    def generate_shop_items(self):
        """Generate shop items.

        Returns a dict with shop items as keys and
        cost and quantity data in a dict or list as value.
        """

        shop_items = {
            "brawlbox": {
                "quantity": 0, "cost": 0, "number": 0
            },
            "starpowers": [],
            "tickets": {
                "quantity": 0, "cost": 0, "number": 0
            },
            "powerpoints": [],
            "gem_skins": [],
            "sp_skins": []
        }
        total = 0

        box_chance = random.randint(0, 99)
        if box_chance in range(0, self.items["brawlbox"][1]):
            total += 1
            shop_items["brawlbox"] = {
                "quantity": 1,
                "cost": self.items["brawlbox"][0],
                "number": total
            }

        if self.can_get_sp:
            sp_chance = random.randint(0, 99)
            if sp_chance in range(0, self.items["brawlbox"][1]):
                sp_brawler, sp = self.get_starpower()
                sp_name = self.ALL_BRAWLERS[sp_brawler][sp]["name"]
                total += 1
                shop_items["starpowers"].append({
                    "quantity": 1,
                    "cost": 2000,
                    "brawler": sp_brawler,
                    "sp": sp,
                    "sp_name": sp_name,
                    "number": total
                })

        ticket_chance = random.randint(0, 99)
        if ticket_chance in range(0, self.items["tickets"][1]):
            total += 1
            shop_items["tickets"] = {
                "quantity": random.randint(1, 5),
                "cost": self.items["tickets"][0],
                "number": total
            }

        powerpoints = self.get_powerpoints(total)
        shop_items["powerpoints"] = powerpoints
        total += len(powerpoints)

        if total < self.max_slots:
            # another SP chance
            if self.can_get_sp:
                sp_chance = random.randint(0, 99)
                if sp_chance in range(0, self.items["brawlbox"][1]):
                    sp_brawler, sp = self.get_starpower()
                    sp_name = self.ALL_BRAWLERS[sp_brawler][sp]["name"]
                    shop_items["starpowers"].append({
                        "quantity": 1,
                        "cost": 2000,
                        "brawler": sp_brawler,
                        "sp": sp,
                        "sp_name": sp_name,
                        "number": total
                    })
                    total += 1

        gem, starpoint = self.get_skins()
        shop_items["gem_skins"] = gem
        shop_items["sp_skins"] = starpoint

        self.shop_items = shop_items

        return shop_items

    def get_starpower(self):
        """Returns brawler name and star power number string."""

        sp_brawler = random.choice(list(self.can_get_sp.keys()))
        sp = random.choice(self.can_get_sp[sp_brawler])

        self.can_get_sp[sp_brawler].remove(sp)
        if not self.can_get_sp[sp_brawler]:
            self.can_get_sp.pop(sp_brawler)

        return sp_brawler, sp

    def get_powerpoints(self, total: int):
        """Returns list containing powerpoints data."""

        if not self.can_get_pp:
            return []

        pp_list = []
        items = list(self.can_get_pp.items())
        random.shuffle(items)
        while True:
            for brawler, threshold in items:
                if threshold < 1:
                    continue
                quantity = random.randint(1, min(threshold, 50))

                total += 1
                pp_list.append({
                    "brawler": brawler,
                    "quantity": quantity,
                    "cost": quantity * self.items["powerpoints"][0],
                    "number": total
                })

                items.remove((brawler, threshold))
                if not len(items):
                    return pp_list
                if self.max_slots == total:
                    return pp_list

    def get_skins(self):
        """Returns shop skins data."""

        gem_skins = []
        sp_skins = []
        # sample for above lists
        # {
        #     "skin":
        #     "brawler":
        #     "cost":
        #     "number": (starts with s)
        # }

        for brawler in self.BRAWLERS_DATA:
            owned = self.BRAWLERS_DATA[brawler]["skins"]
            brawler_skins = self.ALL_BRAWLERS[brawler]["skins"]
            for skin in brawler_skins:
                if skin not in owned:
                    if brawler_skins[skin][0] != -1:
                        gem_skins.append({
                            "skin": skin,
                            "brawler": brawler,
                            "cost": brawler_skins[skin][0]
                        })
                    elif brawler_skins[skin][1] != -1:
                        sp_skins.append({
                            "skin": skin,
                            "brawler": brawler,
                            "cost": brawler_skins[skin][1]
                        })

        random.shuffle(gem_skins)
        random.shuffle(sp_skins)

        gem_skins = gem_skins[:min(self.max_skins[0], len(gem_skins))]
        sp_skins = sp_skins[:min(self.max_skins[1], len(sp_skins))]

        for i, gskin in enumerate(gem_skins, start=1):
            gskin["number"] = "S"+str(i)

        for sskin in sp_skins:
            i += 1
            sskin["number"] = "S"+str(i)

        return (gem_skins, sp_skins)

    def create_items_embeds(self, user: discord.User, next_reset: str):
        """Returns formatted embeds from shop data."""

        timestamp = datetime.utcnow()

        desc = (
            "Use `shop buy` command to buy items!"
            f"\n\nShop will reset in {next_reset}."
        )

        general = discord.Embed(
            colour=EMBED_COLOR,
            description=f"{desc}\n\n**Daily Deals:**",
            timestamp=timestamp
        )

        author_name = f"{user.name}'"
        if author_name[-1] != "s":
            author_name += "s"

        general.set_author(
            name=f"{author_name} Daily Shop", icon_url=user.avatar_url
        )
        general.set_footer(text="Page 1 of 2")

        general = self.brawlbox_field(general)
        general = self.tickets_field(general)
        general = self.starpower_fields(general)
        general = self.powerpoints_fields(general)

        skins = discord.Embed(
            colour=EMBED_COLOR,
            description=f"{desc}\n\n**Skins:**",
            timestamp=timestamp
        )

        skins.set_author(
            name=f"{author_name} Daily Shop", icon_url=user.avatar_url
        )
        skins.set_footer(text="Page 2 of 2")

        skins = self.skins_field(skins)

        return [general, skins]

    def brawlbox_field(self, embed: discord.Embed):
        """Add brawlbox field and return embed."""

        if self.shop_items["brawlbox"]["quantity"]:
            embed.add_field(
                name=(
                    f"{emojis['brawlbox']} Brawl Box"
                    f" [Item #{self.shop_items['brawlbox']['number']}]"
                ),
                value=self.shop_items['brawlbox']['cost'] or "Free!",
                inline=False
            )

        return embed

    def tickets_field(self, embed: discord.Embed):
        """Add tickets field and return embed."""

        shop_items = self.shop_items

        if shop_items["tickets"]["quantity"]:
            embed.add_field(
                name=(
                    f"{emojis['ticket']} Tickets"
                    f" x{shop_items['tickets']['quantity']}"
                    f" [Item #{shop_items['tickets']['number']}]"
                ),
                value=self.shop_items['tickets']['cost'] or "Free!",
                inline=False
            )

        return embed

    def powerpoints_fields(self, embed: discord.Embed):
        """Add powerpoints fields and return embed."""

        shop_items = self.shop_items

        if shop_items["powerpoints"]:
            for item in shop_items["powerpoints"]:
                brawler = item['brawler']
                cost = item["cost"]
                if isinstance(cost, str):
                    cost = "(Bought!)"
                else:
                    cost = f"{emojis['gold']} {cost}"
                embed.add_field(
                    name=(
                        f" {brawler_emojis[brawler]} {brawler}"
                        f" [Item #{item['number']}]"
                    ),
                    value=f"{emojis['powerpoint']} {item['quantity']} {cost}",
                    inline=False
                )

        return embed

    def starpower_fields(self, embed: discord.Embed):
        """Add starpower fields and return embed."""

        shop_items = self.shop_items

        if shop_items["starpowers"]:
            for item in shop_items["starpowers"]:
                brawler = item['brawler']
                sp_num = int(item['sp'][-1])
                cost = item["cost"]
                if isinstance(cost, str):
                    cost = "(Bought!)"
                else:
                    cost = f"{emojis['gold']} {cost}"
                embed.add_field(
                    name=(
                        f"{brawler_emojis[brawler]} {item['sp_name']}"
                        f" {sp_icons[brawler][sp_num-1]}"
                        f" [Item #{item['number']}]"
                    ),
                    value=cost,
                    inline=False
                )

        return embed

    def skins_field(self, embed: discord.Embed):
        """Add skins field and return embed."""

        shop_items = self.shop_items

        # items = ["gem_skins", "sp_skins"]
        if shop_items["gem_skins"]:
            for item in shop_items["gem_skins"]:
                brawler = item["brawler"]
                cost = item["cost"]
                skin = item["skin"]
                number = item["number"]
                if isinstance(cost, str):
                    cost = "Bought!"
                else:
                    cost = f"{emojis['gem']} {cost}"
                embed.add_field(
                    name=(
                        f"{brawler_emojis[brawler]} {skin}"
                        f" {brawler} (Item #{number})"
                    ),
                    value=cost,
                    inline=False
                )

        if shop_items["sp_skins"]:
            for item in shop_items["sp_skins"]:
                brawler = item["brawler"]
                cost = item["cost"]
                skin = item["skin"]
                number = item["number"]
                if isinstance(cost, str):
                    cost = "Bought!"
                else:
                    cost = f"{emojis['starpoints']} {cost}"
                embed.add_field(
                    name=(
                        f"{brawler_emojis[brawler]} {skin}"
                        f" {brawler} (Item #{number})"
                    ),
                    value=cost,
                    inline=False
                )

        return embed

    def to_json(self) -> dict:
        """Returns the shop object as a dict."""

        data = {
            "items": self.shop_items
        }

        return data

    @classmethod
    def from_json(cls, data: dict):
        """Returns a `Shop` instance from data dict.

        `Shop` instances created this way can not be used for
        new shop generation. They can only be used to display
         shop and buy items.
        """

        shop = cls()
        shop.shop_items = data['items']

        return shop

    async def buy_item(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        brawlers: dict,
        item_number: int
    ):
        """Function to handle shop purchases."""

        found = False

        # check for brawl box
        if self.shop_items["brawlbox"]["quantity"]:
            if item_number == self.shop_items["brawlbox"]["number"]:
                if await self.can_not_buy(
                    ctx, item_number, self.shop_items["brawlbox"]
                ):
                    return
                found = True
                await self.buy_brawlbox(ctx, user, config, brawlers)
                self.shop_items["brawlbox"]["cost"] = "Claimed!"

        # check for tickets
        if not found:
            if self.shop_items["tickets"]["quantity"]:
                if item_number == self.shop_items["tickets"]["number"]:
                    if await self.can_not_buy(
                        ctx, item_number, self.shop_items["tickets"]
                    ):
                        return
                    found = True
                    await self.buy_ticket(ctx, user, config)
                    self.shop_items["tickets"]["cost"] = "Claimed!"

        # check for power point
        if not found:
            for item in self.shop_items["powerpoints"]:
                if item_number == item["number"]:
                    if await self.can_not_buy(ctx, item_number, item):
                        return
                    found = True
                    if not await self.buy_powerpoint(
                        ctx, user, config, item
                    ):
                        return
                    item["cost"] = "Bought!"

        # check for star power
        if not found:
            for item in self.shop_items["starpowers"]:
                if item_number == item["number"]:
                    if await self.can_not_buy(ctx, item_number, item):
                        return
                    found = True
                    if not await self.buy_starpower(
                        ctx, user, config, item
                    ):
                        return
                    item["cost"] = "Bought!"

        # error
        if not found:
            await ctx.send(
                f"Item #{item_number} doesn't seem to exist."
                " Please re-check the number!"
            )
            return

        return {"items": self.shop_items}

    async def buy_brawlbox(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        brawlers: dict
    ):
        brawler_data = await config.user(user).brawlers()

        box = Box(brawlers, brawler_data)
        try:
            embed = await box.brawlbox(config.user(user), user)
        except Exception as exc:
            return await ctx.send(
                f"Error \"{exc}\" while opening a Brawl Box."
                " Please notify bot creator using `-report` command."
            )

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(
                "I do not have the permission to embed a link."
                " Please give/ask someone to give me that permission."
            )

    async def buy_ticket(
        self,
        ctx: Context,
        user: discord.User,
        config: Config
    ):
        quantity = self.shop_items["tickets"]["quantity"]

        old = await config.user(user).tickets()
        await config.user(user).tickets.set(old+quantity)

        await ctx.send(f"You recieved {quantity} {emojis['ticket']}!")

    async def buy_powerpoint(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        item_data: dict
    ):
        brawler = item_data["brawler"]
        quantity = item_data["quantity"]
        cost = item_data["cost"]

        gold = await config.user(user).gold()

        if gold < cost:
            await ctx.send(
                f"You do not have enough gold! ({gold}/{cost})"
            )
            return

        msg = await ctx.send(
            f"{user.mention} Buying {quantity} {brawler} power points"
            f" will cost {emojis['gold']} {cost}. Continue?"
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result:
            # User responded with tick
            pass
        else:
            # User responded with cross
            await ctx.send("Purchase cancelled.")
            return False

        async with config.user(user).brawlers() as brawlers:
            brawlers[brawler]['powerpoints'] += quantity
            brawlers[brawler]['total_powerpoints'] += quantity

        await config.user(user).gold.set(gold-cost)

        await ctx.send(f"Bought {quantity} {brawler} power points!")

        return True

    async def buy_starpower(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        item_data: dict
    ):
        brawler = item_data["brawler"]
        cost = item_data["cost"]
        sp = item_data["sp"]
        sp_name = item_data["sp_name"]

        gold = await config.user(user).gold()

        if gold < cost:
            await ctx.send(
                f"You do not have enough gold! ({gold}/{cost})"
            )
            return False

        msg = await ctx.send(
            f"{user.mention} Buying {brawler}'s Star Power **{sp_name}**"
            f" will cost {emojis['gold']} {cost}. Continue?"
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result:
            # User responded with tick
            pass
        else:
            # User responded with cross
            await ctx.send("Purchase cancelled.")
            return False

        async with config.user(user).brawlers() as brawlers:
            brawlers[brawler]["level"] = 10
            brawlers[brawler][sp] = True

        await config.user(user).gold.set(gold-cost)

        await ctx.send(f"Bought {sp_name} Star Power!")

        return True

    async def buy_skin(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        brawlers: dict,
        item_number: int
    ):
        """Function to handle shop purchases."""

        found = False

        # check for gem skins
        for item in self.shop_items["gem_skins"]:
            if item_number == item["number"]:
                if await self.can_not_buy(ctx, item_number, item):
                    return
                found = True
                if not await self.buy_gem_skin(
                    ctx, user, config, item
                ):
                    return
                item["cost"] = "Bought!"

        # check for sp skins
        if not found:
            for item in self.shop_items["sp_skins"]:
                if item_number == item["number"]:
                    if await self.can_not_buy(ctx, item_number, item):
                        return
                    found = True
                    if not await self.buy_star_skin(
                        ctx, user, config, item
                    ):
                        return
                    item["cost"] = "Bought!"

        # error
        if not found:
            await ctx.send(
                f"Skin #{item_number} doesn't seem to exist."
                " Please re-check the number!"
            )
            return

        return {"items": self.shop_items}

    async def buy_gem_skin(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        item_data: dict
    ):
        brawler = item_data["brawler"]
        cost = item_data["cost"]
        skin = item_data["skin"]

        gems = await config.user(user).gems()

        if gems < cost:
            await ctx.send(
                f"You do not have enough gems! ({gems}/{cost})"
            )
            return False

        msg = await ctx.send(
            f"{user.mention} Buying **{skin} {brawler}**"
            f" skin will cost {emojis['gem']} {cost}. Continue?"
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result:
            # User responded with tick
            pass
        else:
            # User responded with cross
            await ctx.send("Purchase cancelled.")
            return False

        async with config.user(user).brawlers() as brawlers:
            brawlers[brawler]["skins"].append(skin)

        await config.user(user).gems.set(gems-cost)

        await ctx.send(f"Bought {skin} {brawler} skin!")

        return True

    async def buy_star_skin(
        self,
        ctx: Context,
        user: discord.User,
        config: Config,
        item_data: dict
    ):
        brawler = item_data["brawler"]
        cost = item_data["cost"]
        skin = item_data["skin"]

        starpoints = await config.user(user).starpoints()

        if starpoints < cost:
            await ctx.send(
                f"You do not have enough gems! ({starpoints}/{cost})"
            )
            return False

        msg = await ctx.send(
            f"{user.mention} Buying **{skin} {brawler}** skin"
            f" will cost {emojis['starpoints']} {cost}. Continue?"
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result:
            # User responded with tick
            pass
        else:
            # User responded with cross
            await ctx.send("Purchase cancelled.")
            return False

        async with config.user(user).brawlers() as brawlers:
            brawlers[brawler]["skins"].append(skin)

        await config.user(user).starpoints.set(starpoints-cost)

        await ctx.send(f"Bought {skin} {brawler} skin!")

        return True

    async def can_not_buy(self, ctx: Context, num: int, item_data: dict):
        if item_data["cost"] in ["Claimed!", "Bought!"]:
            cost = item_data['cost'].lower()[:-1]
            await ctx.send(f"You have already {cost} item #{num}.")
            return True
