import random

import discord

from brawlcord.brawlers import emojis, brawler_emojis

default_stats = {
    "trophies": 0,
    "pb": 0,
    "rank": 1,
    "level": 1,
    "powerpoints": 0,
    "total_powerpoints": 0,
    "skins": ["Default"],
    "sp1": False,
    "sp2": False
}


class Box:
    """A class to represent Boxes."""
    
    # odds
    rares = 2.7103,
    superrares = 1.2218,
    epic = 0.5527
    mythic = 0.2521
    legendary = 0.1115
    starpower: int

    # number of powerpoints required to max
    max_pp = 1410
    
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

                if sp1 == False and sp2 == True:
                    self.can_get_sp[brawler] = ['sp1']
                elif sp1 == True and sp2 == False:
                    self.can_get_sp[brawler] = ['sp2']
                elif sp1 == False and sp2 == False:
                    self.can_get_sp[brawler] = ['sp1', 'sp2']
                else:
                    pass

    def weighted_random(self, lower, upper, avg):
        avg_low = (avg + lower) / 2
        avg_high = (upper + avg) / 2
        
        p_high = (avg - avg_low) / (avg_high - avg_low)

        # return p_high

        chance = random.random() 

        if chance < p_high:
            return random.randint(avg, upper)
        else:
            return random.randint(lower, avg)
    
    def split_in_integers(self, number, num_of_pieces):
        """Split a number into number of integers."""
        def accel_asc(n):
            a = [0 for i in range(n + 1)]
            k = 1
            y = n - 1
            while k != 0:
                x = a[k - 1] + 1
                k -= 1
                while 2 * x <= y:
                    a[k] = x
                    y -= x
                    k += 1
                l = k + 1
                while x <= y:
                    a[k] = x
                    a[l] = y
                    yield a[:k + 2]
                    x += 1
                    y -= 1
                a[k] = x + y
                y = x + y - 1
                yield a[:k + 1]
        
        pieces = list(accel_asc(number))
        random.shuffle(pieces)
        
        for piece in pieces:
            if len(piece) == num_of_pieces:
                return piece

    async def brawlbox(self, conf, user):
        """Function to handle brawl box openings."""
    
        gold = self.weighted_random(12, 70, 19) 

        stacks = 2
        
        if len(self.can_get_pp) == 0:
            gold *= 3
            stacks = 0

        elif len(self.can_get_pp) == 1:
            gold *= 2
            stacks = 1
        
        powerpoints = int(self.weighted_random(9, 25, 16))

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
                            pp_str += f"\n{brawler_emojis[brawler]} **{brawler}:** {emojis['powerpoint']} {piece}"
                    else:
                        continue
                    break
        
        if not pp_str:
            pp_str = "No powerpoints"
        
        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)

        embed = discord.Embed(color=0xFFA232, title="Brawl Box")
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}", inline=False)
        embed.add_field(name="Power Points", value=pp_str.strip(), inline=False)

        rarity = self.brawler_rarity()
        
        embed = await self.unlock_brawler(rarity, conf, embed)
        
        return embed

    async def unlock_brawler(self, rarity, conf, embed):
        brawler = random.choice(self.can_unlock[rarity])
        async with conf.brawlers() as brawlers:
            brawlers[brawler] = default_stats
        embed.add_field(name=f"{rarity} Brawler", value=f"{brawler_emojis[brawler]} {brawler}")
        
        return embed

    def brawler_rarity(self):
        """
        Return rarity by generating a random number, calculating odds and checking 
        the rarities from which user can unlock a brawler.
        """
        # odds calculation below

        # testing
        # rarity = random.choice(list(self.can_unlock.keys()))
        rarity = "Legendary"

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
            if not self.can_unlock[rarity]:
                rarity = lower_rarity(rarity)
                if not rarity:
                    break
            else:
                break

        return rarity

class GameModes:
    """A class to represent game modes."""
