import random

import discord

from brawlcord.brawlers import emojis, brawler_emojis

# class GameSession:
#     """A class to represent and hold current game sessions per server."""

#     timer: int
#     guild: discord.Guild
#     message_id: int
#     reacted: bool = False
#     teamred: Set[discord.Member] = set()
#     teamblue: Set[discord.Member] = set()

#     def __init__(self, **kwargs):
#         self.guild: dict = kwargs.pop("guild")
#         self.timer: int = kwargs.pop("timer")
#         self.reacted = False
#         self.message_id = 0
#         teamred: Set[discord.Member] = set()
#         teamblue: Set[discord.Member] = set()


class Box:
    """A class to represent Boxes."""
    
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
            # if all_brawlers[brawler]["unlockTrp"] >= 0:
            #     # it is a trophy road brawler 
            #     continue

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

        return embed
        
class GameModes:
    """A class to represent game modes."""
