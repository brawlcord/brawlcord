import random

import discord

from redbot.core.utils.menus import DEFAULT_CONTROLS, menu, start_adding_reactions
from redbot.core.commands.context import Context
from redbot.core.utils.predicates import ReactionPredicate

from brawlcord.brawlers import *


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

gamemode_emotes = {
    "Big Game": "<:big_game:645925169344282624>",
    "Bounty": "<:bounty:645925169252270081>",
    "Boss Fight": "<:bossfight:645925170397052929>",
    "Brawl Ball": "<:brawlball:645925169650466816>",
    "Gem Grab": "<:gemgrab:645925169730289664>",
    "Duo Showdown": "<:duo_showdown:645925169805656076>",
    "Heist": "<:heist:645925170195988491>",
    "raid": "<:raid:645925170397052929>",
    "Siege": "<:siege:645925170481201163>",
    "Solo Showdown": "<:solo_showdown:645925170539921428>",
    "Robo Rumble": "<:roborumble:645925170594316288>",
    "Lone Star": "<:lonestar:645925170610962452>",
    "Takedown": "<:takedown:645925171034587146>",
}

spawn_text = {
    "Nita": "Bear",
    "Penny": "Cannon",
    "Jessie": "Turrent",
    "Pam": "Healing Station",
    "8-Bit": "Turret"
}

brawlers_map = {
    "Shelly": Shelly,
    "Nita": Nita,
    "Colt": Colt,
    "Bull": Bull,
    "Jessie": Jessie
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
        self.td = 3 # token doubler 

        # number of powerpoints required to max
        self.max_pp = 1410

        self.pop = ["Power Points", "Rare", "Super Rare", "Epic", "Mythic", "Legendary", "Star Power"]
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
        
        rarities = []
        starpowers = 0
        stacks = 0
        
        selected = random.choices(population=self.pop, weights=self.weights, k=2)

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
        
        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)

        embed = discord.Embed(color=0xFFA232, title=f"{emojis['brawlbox']} Brawl Box")
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}", inline=False)
        if pp_str:
            embed.add_field(name="Power Points", value=pp_str.strip(), inline=False)

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
            embed.add_field(name="Token Doubler", value=f"{emojis['tokendoubler']} 200")
        elif chance <= self.gems:
            try:
                old_gems = await conf.gems()
            except:
                print("error with gems")
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
        
        selected = random.choices(population=self.pop, weights=self.weights, k=5)

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
                            pp_str += f"\n{brawler_emojis[brawler]} **{brawler}:** {emojis['powerpoint']} {piece}"
                    else:
                        continue
                    break
        
        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)

        embed = discord.Embed(color=0xFFA232, title=f"Big Box {emojis['bigbox']}")
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}", inline=False)
        if pp_str:
            embed.add_field(name="Power Points", value=pp_str.strip(), inline=False)

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
            embed.add_field(name="Token Doubler", value=f"{emojis['tokendoubler']} 200")
        elif chance <= self.gems:
            old_gems = await conf.gems()
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
        
        selected = random.choices(population=self.pop, weights=self.weights, k=9)

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
                            pp_str += f"\n{brawler_emojis[brawler]} **{brawler}:** {emojis['powerpoint']} {piece}"
                    else:
                        continue
                    break
        
        old_gold = await conf.gold()
        await conf.gold.set(old_gold + gold)
        
        embed = discord.Embed(color=0xFFA232, title=f"Mega Box {emojis['megabox']}")
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(name="Gold", value=f"{emojis['gold']} {gold}", inline=False)
        if pp_str:
            embed.add_field(name="Power Points", value=pp_str.strip(), inline=False)

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
            embed.add_field(name="Token Doubler", value=f"{emojis['tokendoubler']} 200")
        elif chance <= self.gems:
            try:
                old_gems = await conf.gems()
            except:
                print("error with gems")
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
        async with conf.brawlers() as brawlers:
            brawlers[brawler] = default_stats
        embed.add_field(name=f"New {rarity} Brawler :tada:", 
                value=f"{brawler_emojis[brawler]} {brawler}", inline=False)
        
        return embed

    def check_rarity(self, rarity):
        """
        Return rarity by checking the rarities from which user can unlock a brawler.
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
        print(self.can_get_sp)
        sp = random.choice(self.can_get_sp[sp_brawler])

        self.can_get_sp[sp_brawler].remove(sp)

        sp_name = self.BRAWLERS[sp_brawler][sp]["name"]
        sp_desc = self.BRAWLERS[sp_brawler][sp]["desc"]
        sp_index = int(sp[2]) - 1

        sp_str = (f"{sp_icons[sp_brawler][sp_index]} {sp_name} - {brawler_emojis[sp_brawler]}" 
                f" {sp_brawler}\n> {sp_desc}")

        async with conf.brawlers() as brawlers:
            brawlers[sp_brawler]["level"] = 10
            brawlers[sp_brawler][sp] = True
        
        embed.add_field(name="New Star Power :tada:", value=sp_str, inline=False)

        return embed

class GameModes:
    """A class to represent game modes."""

    def __init__(self, ctx: Context, user: discord.User, opponent: discord.User, conf, brawlers):
        # defining class variables 
        
        self.user = user
        self.opponent = opponent

        self.first: Brawler
        self.second: Brawler
        self.first_player: discord.User
        self.second_player: discord.User
        self.first_brawler: str
        self.second_brawler: str
        self.fp_brawler_level: int
        self.sp_brawler_level: int
        
        self.guild = ctx.guild
        self.conf = conf
        self.BRAWLERS = brawlers
        
        self.first_attacks = 0
        self.second_attacks = 0
        
        self.first_invincibility = False
        self.second_invincibility = False

        self.first_spawn = None
        self.second_spawn = None

    async def initialize(self, ctx: Context):
        user = self.user
        opponent = self.opponent

        user_brawler = await self.get_player_stat(user, "selected", is_iter=True, substat="brawler")
        brawler_data = await self.get_player_stat(user, "brawlers", is_iter=True, substat=user_brawler)
        user_brawler_level = brawler_data['level']

        gamemode = await self.get_player_stat(user, "selected", is_iter=True, substat="gamemode")

        ub: Brawler = brawlers_map[user_brawler](self.BRAWLERS, user_brawler)

        if opponent:
            opp_brawler = await self.get_player_stat(opponent, "selected", is_iter=True, substat="brawler")
            opp_data = await self.get_player_stat(opponent, "brawlers", is_iter=True, substat=opp_brawler)
            opp_brawler_level = brawler_data['level']

            # ob: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)

        else:
            opponent = self.guild.me
            opp_brawler, opp_brawler_level, opp_brawler_sp = self.matchmaking(user_brawler_level)

        ob: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)

        if opponent != self.guild.me:
            try:
                msg = await opponent.send(f"{user.mention} has challenged you for a brawl."
                    f" Game Mode: **{gamemode}**. Accept?")
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

                pred = ReactionPredicate.yes_or_no(msg, opponent)
                await ctx.bot.wait_for("reaction_add", check=pred)
                if pred.result is True:
                    # User responded with tick
                    pass
                else:
                    # User responded with cross
                    return await ctx.send(f"{user.mention} {opponent.mention} Brawl cancelled."
                    f" Reason: {opponent.name} rejected the challenge.")    
            except:
                return await ctx.send(f"{user.mention} {opponent.mention} Brawl cancelled." 
                    f" Reason: Unable to DM {opponent.name}. DMs are required to brawl!")
          
        first_move_chance = random.randint(1, 2)
        if first_move_chance == 1:
            self.first = ub
            self.second = ob
            self.first_player = user
            self.second_player = opponent
            self.first_brawler = user_brawler
            self.second_brawler = opp_brawler
            self.fp_brawler_level = user_brawler_level
            self.sp_brawler_level = opp_brawler_level
        else:
            self.first = ob
            self.second = ub
            self.first_player = opponent
            self.second_player = user
            self.first_brawler = opp_brawler
            self.second_brawler = user_brawler
            self.sp_brawler_level = user_brawler_level
            self.fp_brawler_level = opp_brawler_level
    
        self.sfh = self.first._health(self.fp_brawler_level) # static first health
        self.ssh = self.second._health(self.sp_brawler_level) # static second health
        
        self.first_health = self.sfh
        self.second_health = self.ssh

        try:
            self.first_spawn_str = spawn_text[self.first_brawler]
        except:
            self.first_spawn_str = ""
        
        try:
            self.second_spawn_str = spawn_text[self.second_brawler]
        except:
            self.second_spawn_str = ""
    
        winner, loser = await self.gemgrab(ctx)

        return self.first_player, self.second_player, winner, loser
    
    async def gemgrab(self, ctx):
        """Function to play Gem Grab!"""
                
        first_gems = 0
        second_gems = 0
        
        while True:
            if self.second_player != self.guild.me:
                try:
                    await self.second_player.send("Waiting for opponent to pick a move...")
                except:
                    return await ctx.send(f"{self.first_player.mention} {self.second_player.mention} Brawl cancelled."
                    f" Reason: Unable to DM {self.second_player.name}. DMs are required to brawl!")
                
            if self.first_attacks >= 6:
                first_can_super = True
                end = 4
            else:
                first_can_super = False
                end = 3
            if self.second_spawn:
                end += 1

        
            if self.first_player != self.guild.me:
                desc = "Pick a move by typing the corresponding move number below."
                embed = discord.Embed(color=0xFFA232, title=f"Brawl against {self.second_player.name}")
                embed.set_author(name=self.first_player.name, icon_url=self.first_player.avatar_url)

                embed.add_field(name="Your Brawler", 
                            value=f"{brawler_emojis[self.first_brawler]} {self.first_brawler}")
                embed.add_field(name="Your Health", 
                            value=f"{emojis['health']} {int(self.first_health)}")
                embed.add_field(name="Your Gems", 
                            value=f"{gamemode_emotes['Gem Grab']} {first_gems}")
                
                if self.first_spawn:
                    embed.add_field(name=f"Your {self.first_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(self.first_spawn)}", inline=False)
                
                embed.add_field(name="Opponent's Brawler", 
                            value=f"{brawler_emojis[self.second_brawler]} {self.second_brawler}")
                embed.add_field(name="Opponent's Health", 
                            value=f"{emojis['health']} {int(self.second_health)}")
                embed.add_field(name="Opponent's Gems", 
                            value=f"{gamemode_emotes['Gem Grab']} {second_gems}")

                if self.second_spawn:
                    embed.add_field(name=f"Opponent's {self.second_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(self.second_spawn)}", inline=False)
                
                moves = (f"1. Attack\n2. Collect gem\n3. Dodge next move"
                            f"\n{'4. Use Super' if first_can_super else ''}").strip()
                
                if first_can_super and not self.second_spawn:
                    moves = "1. Attack\n2. Collect gem\n3. Dodge next move\n4. Use Super"
                elif first_can_super and self.second_spawn:
                    moves = ("1. Attack\n2. Collect gem\n3. Dodge next move"
                        f"\n4. Use Super\n5. Attack {self.second_spawn_str}")
                elif not first_can_super and self.second_spawn:
                    moves = ("1. Attack\n2. Collect gem\n3. Dodge next move"
                        f"\n4. Attack enemy {self.second_spawn_str}")
                else:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move"

                embed.add_field(name="Available Moves", value=moves, inline=False)

                try:
                    msg = await self.first_player.send(embed=embed)

                    react_emojis = ReactionPredicate.NUMBER_EMOJIS[1:end+1]
                    start_adding_reactions(msg, react_emojis)

                    pred = ReactionPredicate.with_emojis(react_emojis, msg)
                    await ctx.bot.wait_for("reaction_add", check=pred)

                    # pred.result is  the index of the letter in `emojis`

                    choice = pred.result + 1
                except:
                    return await ctx.send(f"{self.first_player.mention} {self.second_player.mention}" 
                            f"Reason: Unable to DM {self.first_player.name}. DMs are required to brawl!")

            else:
                # develop bot logic
                choice = random.randint(1, end)
            
            if choice == 1:
                damage = self.first._attack(self.fp_brawler_level)
                if not self.second_invincibility:
                    self.second_health -= damage
                    self.first_attacks += 1
                else:
                    self.second_invincibility = False
            elif choice == 2:
                first_gems += 1
                if self.second_invincibility:
                    self.second_invincibility = False
            elif choice == 3:
                self.first_invincibility = True
                if self.second_invincibility:
                    self.second_invincibility = False
            elif choice == 4:
                if first_can_super:
                    damage, self.first_spawn = self.first._ult(self.fp_brawler_level)
                    self.first_attacks = 0
                    if not self.second_invincibility:
                        self.second_health -= damage
                    else:
                        self.second_health -= damage * 0.5
                        self.second_invincibility = False
                else:
                    self.second_spawn -= self.first._attack(self.fp_brawler_level)
            elif choice == 5:
                self.second_spawn -= self.first._attack(self.fp_brawler_level)
            
            if self.first_spawn:
                damage = self.first._spawn(self.fp_brawler_level)
                if not self.second_invincibility:
                    self.second_health -= damage
                    self.first_attacks += 1
                else:
                    self.second_invincibility = False

            winner, loser = self.check_if_win(first_gems, second_gems)
            
            if winner == False:
                pass
            else:
                break
            
            if self.first_player != self.guild.me:
                await self.first_player.send("Waiting for opponent to pick a move...")
            
            if self.second_attacks >= 6:
                second_can_super = True
                end = 4
            else:
                second_can_super = False
                end = 3

            if self.second_player != self.guild.me:
                desc = "Pick a move by typing the corresponding move number below."
                embed = discord.Embed(color=0xFFA232, title=f"Brawl against {self.first_player.name}")
                embed.set_author(name=self.second_player.name, icon_url=self.second_player.avatar_url)
                
                embed.add_field(name="Your Brawler",
                            value=f"{brawler_emojis[self.second_brawler]} {self.second_brawler}")
                embed.add_field(name="Your Health", 
                            value=f"{emojis['health']} {int(self.second_health)}")
                embed.add_field(name="Your Gems", 
                            value=f"{gamemode_emotes['Gem Grab']} {second_gems}")
                
                if self.second_spawn:
                    embed.add_field(name=f"Your {self.second_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(self.second_spawn)}", inline=False)
                
                embed.add_field(name="Opponent's Brawler", 
                            value=f"{brawler_emojis[self.first_brawler]} {self.first_brawler}")
                embed.add_field(name="Opponent's Health", 
                            value=f"{emojis['health']} {int(self.first_health)}")
                embed.add_field(name="Opponent's Gems", 
                            value=f"{gamemode_emotes['Gem Grab']} {first_gems}")
                
                if self.first_spawn:
                    embed.add_field(name=f"Opponent's {self.first_spawn_str}'s Health", 
                            value=f"{emojis['health']} {int(self.first_spawn)}", inline=False)
                
                if second_can_super and not self.first_spawn:
                    moves = "1. Attack\n2. Collect gem\n3. Dodge next move\n4. Use Super"
                elif second_can_super and self.first_spawn:
                    moves = ("1. Attack\n2. Collect gem\n3. Dodge next move"
                        f"\n4. Use Super\n5. Attack {self.first_spawn_str}")
                elif not second_can_super and self.first_spawn:
                    moves = ("1. Attack\n2. Collect gem\n3. Dodge next move"
                        f"\n4. Attack enemy {self.first_spawn_str}")
                else:
                    moves = f"1. Attack\n2. Collect gem\n3. Dodge next move"
                
                embed.add_field(name="Available Moves", value=moves, inline=False)

                msg = await self.second_player.send(embed=embed)

                react_emojis = ReactionPredicate.NUMBER_EMOJIS[1:end+1]
                start_adding_reactions(msg, react_emojis)

                pred = ReactionPredicate.with_emojis(react_emojis, msg)
                await ctx.bot.wait_for("reaction_add", check=pred)

                # pred.result is  the index of the letter in `emojis`

                choice = pred.result + 1

            else:
                # develop bot logic
                choice = random.randint(1, end)

            if choice == 1:
                damage = self.second._attack(self.sp_brawler_level)
                if not self.first_invincibility:
                    self.first_health -= damage
                    self.second_attacks += 1
                else:
                    self.first_invincibility = False
            elif choice == 2:
                second_gems += 1
                if self.first_invincibility:
                    self.first_invincibility = False
            elif choice == 3:
                self.second_invincibility = True
                if self.first_invincibility:
                    self.first_invincibility = False
            elif choice == 4:
                if second_can_super:
                    damage, self.second_spawn = self.second._ult(self.sp_brawler_level)
                    self.second_attacks = 0
                    if not self.first_invincibility:
                        self.first_health -= damage
                    else:
                        self.first_health -= damage * 0.5
                        self.first_invincibility = False
                else:
                    self.first_spawn -= self.second._attack(self.sp_brawler_level)
            elif choice == 5:
                self.first_spawn -= self.second._attack(self.sp_brawler_level)

            if self.second_spawn:
                damage = self.second._spawn(self.sp_brawler_level)
                if not self.first_invincibility:
                    self.first_health -= damage
                    self.second_attacks += 1
                else:
                    self.second_invincibility = False
            
            winner, loser = self.check_if_win(first_gems, second_gems)
            
            if winner == False:
                pass
            else:
                break
         
        return winner, loser

    def check_if_win(self, first_gems, second_gems):
        if (self.second_health <= 0 and self.first_health > 0) or (first_gems >= 10 and second_gems < 10):
            winner = self.first_player
            loser = self.second_player
        elif (self.first_health <= 0 and self.second_health > 0) or (second_gems >= 10 and first_gems < 10):
            winner = self.second_player
            loser = self.first_player
        elif (self.first_health <= 0 and self.second_health <= 0) or (second_gems >= 10 and first_gems >= 10):
            winner = None
            loser = None
        else:
            winner = False
            loser = False

        return winner, loser
    
    async def get_player_stat(self, user: discord.User, stat: str, is_iter=False, substat: str = None):
        """Get stats of a player."""

        if not is_iter:
            return await getattr(self.conf(user), stat)()

        async with getattr(self.conf(user), stat)() as stat:
            if not substat:
                return stat
            else:
                return stat[substat]

    def matchmaking(self, brawler_level: int):
        """Get an opponent!"""

        opp_brawler = random.choice(list(self.BRAWLERS))

        opp_brawler_level = random.randint(brawler_level-1, brawler_level+1)
        opp_brawler_sp = None

        if opp_brawler_level > 10:
            opp_brawler_level = 10
            opp_brawler_sp = random.randint(1, 2)

        if opp_brawler_level < 1:
            opp_brawler_level = 1

        return opp_brawler, opp_brawler_level, opp_brawler_sp
