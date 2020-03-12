import asyncio
import random
from math import ceil

import discord
from redbot.core import Config
from redbot.core.commands.context import Context
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from .brawlers import Brawler, brawlers_map
from .brawlhelp import EMBED_COLOR
from .emojis import brawler_emojis, emojis, gamemode_emotes
from .errors import UserRejected

spawn_text = {
    "Nita": "Bear",
    "Penny": "Cannon",
    "Jessie": "Turrent",
    "Pam": "Healing Station",
    "8-Bit": "Turret"
}

healing_over_time = 100
healing_time = 3


class Player:
    """A class for Player data and stats."""

    def __init__(self, user: discord.User, brawler: Brawler, level: int):
        self.player = user

        self.attacks = 0

        self.invincibility = False

        self.respawning = None
        self.is_respawning = False

        self.spawn = None

        self.brawler = brawler
        self.brawler_name = brawler.name
        self.brawler_level = level

        self.static_health = self.brawler._health(self.brawler_level)
        self.health = self.static_health

        self.can_super = False

        self.last_attack = -1  # round number when last attacked

        try:
            self.spawn_str: str = spawn_text[self.brawler_name]
        except KeyError:
            self.spawn_str = ""

    def gemgrab(self):
        self.gems = 0
        self.dropped = 0

    def showdown(self):
        self.powerups = 1

    def _to_json(self) -> dict:
        """Return a dict with player data"""

        return {
            "player": self.player,
            "brawler": self.brawler,
            "brawler_name": self.brawler_name,
            "brawler_level": self.brawler_level,
            "attacks": self.attacks,
            "invincibility": self.invincibility,
            "respawning": self.respawning,
            "spawn": self.spawn,
            "static_health": self.static_health,
            "health": self.health,
            "spawn_str": self.spawn_str
        }


class GameMode:
    """Base class for game modes."""

    def __init__(
        self,
        ctx: Context,
        user: discord.User,
        opponent: discord.User,
        conf: Config,
        brawlers: dict
    ):
        # defining class variables

        self.user = user
        self.opponent = opponent

        self.ctx = ctx
        self.conf = conf
        self.guild = ctx.guild
        self.BRAWLERS = brawlers

    async def initialize(self, ctx: Context):
        user = self.user
        opponent = self.opponent

        user_brawler = await self.get_player_stat(
            user, "selected", is_iter=True, substat="brawler")
        brawler_data = await self.get_player_stat(
            user, "brawlers", is_iter=True, substat=user_brawler)
        user_brawler_level = brawler_data['level']

        gamemode = await self.get_player_stat(
            user, "selected", is_iter=True, substat="gamemode")

        ub: Brawler = brawlers_map[user_brawler](self.BRAWLERS, user_brawler)

        if opponent:
            opp_brawler = await self.get_player_stat(
                opponent, "selected", is_iter=True, substat="brawler")
            # opp_data = await self.get_player_stat(
            #     opponent, "brawlers", is_iter=True, substat=opp_brawler)
            opp_brawler_level = brawler_data['level']

        else:
            opponent = self.guild.me
            (
                opp_brawler,
                opp_brawler_level,
                opp_brawler_sp
            ) = self.matchmaking(user_brawler_level)

        ob: Brawler = brawlers_map[opp_brawler](self.BRAWLERS, opp_brawler)

        if opponent != self.guild.me:
            if user != self.guild.me:
                try:
                    msg = await user.send(
                        f"Waiting for {opponent} to accept the challenge."
                    )
                except discord.Forbidden:
                    await ctx.send(
                        f"{user.mention} {opponent.mention} Brawl cancelled."
                        f" Reason: Unable to DM {user.name}."
                        " DMs are required to brawl!"
                    )
                    raise
            try:
                msg = await opponent.send(
                    f"{user} has challenged you for a brawl."
                    f" Game Mode: **{gamemode}**. Accept?"
                )
            except discord.Forbidden:
                await ctx.send(
                    f"{user.mention} {opponent.mention} Brawl cancelled."
                    f" Reason: Unable to DM {opponent.name}."
                    " DMs are required to brawl!"
                )
                raise

            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

            pred = ReactionPredicate.yes_or_no(msg, opponent)
            try:
                await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(
                    f"{user.mention} {opponent.mention} Brawl cancelled."
                    f" Reason: {opponent.name} did not accept the challenge."
                    )
                raise asyncio.TimeoutError

            if pred.result is True:
                # User responded with tick
                pass
            else:
                # User responded with cross
                await ctx.send(
                    f"{user.mention} {opponent.mention} Brawl cancelled."
                    f" Reason: {opponent.name} rejected the challenge."
                )
                raise UserRejected

        first_move_chance = random.randint(1, 2)

        if first_move_chance == 1:
            self.first = Player(user, ub, user_brawler_level)
            self.second = Player(opponent, ob, opp_brawler_level)
        else:
            self.first = Player(opponent, ob, opp_brawler_level)
            self.second = Player(user, ub, user_brawler_level)

        return self.first.player, self.second.player

    async def play(self, ctx: Context) -> (discord.User, discord.User):
        """Begins the game"""
        pass

    async def get_player_stat(
        self,
        user: discord.User,
        stat: str,
        is_iter=False,
        substat: str = None
    ):
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

    async def send_waiting_message(self, ctx, first_player, second_player):
        """Send the waiting message to the second player."""

        if second_player != self.guild.me:
            try:
                await second_player.send(
                    "Waiting for opponent to pick a move..."
                )
            except discord.Forbidden:
                await ctx.send(
                    f"{first_player.mention} {second_player.mention} Brawl"
                    f" cancelled. Reason: Unable to DM {second_player.name}."
                    " DMs are required to brawl!"
                )
                raise

    async def update_stats(
        self, winner: discord.User, loser: discord.User, game_type="3v3"
    ):
        """Update wins/loss stats of both players."""
        if not winner and not loser:
            # in case of draw, winner and loser are "None"
            return

        async with self.conf(winner).brawl_stats() as brawl_stats:
            brawl_stats[game_type][0] += 1

        async with self.conf(loser).brawl_stats() as brawl_stats:
            brawl_stats[game_type][1] += 1

    def check_if_win(self, first: Player, second: Player):
        pass

    async def set_embed(self, ctx: Context, first: Player, second: Player):
        pass

    def set_embed_fields(
        self,
        embed: discord.Embed,
        player: Player,
        super_emote: str,
        opponent=False
    ):
        pass

    def moves_str(self, first: Player, second: Player):
        pass

    async def get_user_choice(
        self, ctx: Context, embed, end, first_player, second_player
    ):
        try:
            msg = await first_player.send(embed=embed)

            react_emojis = ReactionPredicate.NUMBER_EMOJIS[1:end+1]
            start_adding_reactions(msg, react_emojis)

            pred = ReactionPredicate.with_emojis(react_emojis, msg)
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)

            # pred.result is  the index of the number in `emojis`
            return pred.result + 1
        except asyncio.TimeoutError:
            await ctx.send(f"{first_player.name} took too long to respond.")
            raise asyncio.TimeoutError
        except discord.Forbidden:
            await ctx.send(
                f"{first_player.mention} {second_player.mention}"
                f" Reason: Unable to DM {first_player.name}."
                " DMs are required to brawl!"
            )
            raise

    def move_handler(
        self, choice: int, first: Player, second: Player, round_num: int
    ):
        """Handle user and spawn actions"""
        pass

    def _move_attack(self, first: Player, second: Player, round_num: int):
        first.last_attack = round_num

        damage = first.brawler._attack(first.brawler_level)
        if not second.invincibility:
            second.health -= damage
            first.attacks += 1
        else:
            second.invincibility = False

    def _move_invinc(self, first: Player, second: Player):
        first.invincibility = True
        if second.invincibility:
            second.invincibility = False

    def _move_super(self, first: Player, second: Player, round_num: int):
        first.last_attack = round_num

        vals, first.spawn = first.brawler._ult(first.brawler_level)
        first.attacks = 0
        if isinstance(vals, list):
            # heal
            first.health += vals[0]
            if first.health > first.static_health:
                first.health = first.static_health

            # hardcoding for Mortis to both
            # deal damage and heal
            vals = vals[0]
            if first.brawler_name != "Mortis":
                return

        if not second.invincibility:
            second.health -= vals
        else:
            second.health -= (vals * 0.5)
            second.invincibility = False

    def _move_attack_spawn(self, first: Player, second: Player):
        second.spawn -= first.brawler._attack(first.brawler_level)

    def _move_spawn_attack(self, first: Player, second: Player):
        if first.spawn:
            vals = first.brawler._spawn(first.brawler_level)
            if isinstance(vals, list):
                # heal
                first.health += vals[0]
                if first.health > first.static_health:
                    first.health = first.static_health
            else:
                if not second.invincibility:
                    second.health -= vals
                    first.attacks += 1
                else:
                    second.invincibility = False

    def respawning(self, player: Player):
        player.is_respawning = True
        player.health = player.static_health

    def initial_fields(
        self,
        embed: discord.Embed,
        player: Player,
        super_emote: str,
        opponent=False
    ):

        if opponent:
            iden = "Opponent's"
        else:
            iden = "Your"
        embed.add_field(
            name=f"{iden} Brawler",
            value=(
                f"{brawler_emojis[player.brawler_name]}"
                f" {player.brawler_name} {super_emote}"
            )
        )

        embed.add_field(
            name=f"{iden} Health",
            value=f"{emojis['health']} {int(player.health)}"
        )

        return embed

    def spawn_field(
        self,
        embed: discord.Embed,
        player: Player,
        opponent=False
    ):

        if opponent:
            iden = "Opponent's"
        else:
            iden = "Your"

        if player.spawn:
            if player.spawn > 0:
                embed.add_field(
                    name=f"{iden} {player.spawn_str}'s Health",
                    value=f"{emojis['health']} {int(player.spawn)}",
                    inline=False
                )

        return embed

    async def time_up(self, winner, loser):
        if winner is False:
            # winner and loser are "None" when draw
            winner = None
            loser = None

            try:
                await self.first.player.send(
                    f"Time's up. Match ended in a draw."
                )
            except Exception:
                pass  # bot user
            try:
                await self.second.player.send(
                    f"Time's up. Match ended in a draw."
                )
            except Exception:
                pass  # bot user

        return winner, loser

    def healing(self, round_num: int, player: Player):
        """Heal Player over time."""

        if player.last_attack + healing_time < round_num:
            player.health += healing_over_time
            if player.health > player.static_health:
                player.health = player.static_health


class GemGrab(GameMode):
    """Class to represent Gem Grab."""

    def __init__(self, ctx, user, opponent, conf, brawlers):
        super().__init__(ctx, user, opponent, conf, brawlers)

    async def initialize(self, ctx):
        first, second = await super().initialize(ctx)

        self.first.gemgrab()
        self.second.gemgrab()

        return first, second

    async def play(self, ctx: Context) -> (discord.User, discord.User):
        """Function to run the game"""

        i = 0
        while i < 150:
            # game ends after 75th round
            if i % 2 == 0:
                first = self.first
                second = self.second
            else:
                first = self.second
                second = self.first

            if first.is_respawning:
                try:
                    await first.player.send("You are respawning!")
                except Exception:
                    pass
            else:

                self.healing(i, first)

                try:
                    await self.send_waiting_message(
                        ctx, first.player, second.player
                    )
                except discord.Forbidden:
                    raise

                if not second.is_respawning:
                    if first.attacks >= 6:
                        first.can_super = True
                        end = 4
                    else:
                        first.can_super = False
                        end = 3
                else:
                    end = 3

                if second.spawn:
                    if second.spawn > 0:
                        end += 1
                    else:
                        second.spawn = None

                if first.player != self.guild.me:
                    embed = await self.set_embed(ctx, first, second)
                    try:
                        choice = await self.get_user_choice(
                            ctx, embed, end, first.player, second.player)
                    except asyncio.TimeoutError:
                        winner, loser = second.player, first.player
                        break
                else:
                    # develop bot logic
                    choice = random.randint(1, end)

                self.move_handler(choice, first, second, i)

                if second.health <= 0:
                    self.respawning(second)
                    second.dropped = ceil(second.gems * 0.5)
                    second.gems -= second.dropped

                    try:
                        await first.player.send(
                            f"Opponent defeated! Respawning next round."
                        )
                    except Exception:
                        pass  # bot user
                    try:
                        await second.player.send(
                            f"You are defeated! Respawning next round."
                        )
                    except Exception:
                        pass  # bot user

                    # go to next loop
                    i += 1
                    continue

            winner, loser = self.check_if_win(first, second)

            if winner is False:
                pass
            else:
                break
            # go to next loop
            i += 1

        # time up
        winner, loser = await self.time_up(winner, loser)

        await self.update_stats(winner, loser)

        return winner, loser

    def check_if_win(self, first: Player, second: Player):
        if first.gems >= 10 and second.gems < 10:
            winner = first.player
            loser = second.player
        elif second.gems >= 10 and first.gems < 10:
            winner = second.player
            loser = first.player
        elif second.gems >= 10 and first.gems >= 10:
            winner = None
            loser = None
        else:
            winner = False
            loser = False

        return winner, loser

    async def set_embed(self, ctx: Context, first: Player, second: Player):
        if first.can_super:
            self_super_emote = emojis['superready']
        else:
            self_super_emote = emojis['supernotready']

        if second.can_super:
            opp_super_emote = emojis['superready']
        else:
            opp_super_emote = emojis['supernotready']

        embed = discord.Embed(
            color=EMBED_COLOR,
            title=f"Brawl against {second.player.name}"
        )
        embed.set_author(
            name=first.player.name, icon_url=first.player.avatar_url
        )

        embed = self.set_embed_fields(embed, first, self_super_emote, False)

        embed = self.set_embed_fields(embed, second, opp_super_emote, True)

        moves = self.moves_str(first, second)

        embed.add_field(name="Available Moves", value=moves, inline=False)

        return embed

    def moves_str(self, first: Player, second: Player):
        if not second.is_respawning:
            if first.can_super and not second.spawn:
                moves = (
                    "1. Attack\n2. Try to collect gem\n"
                    "3. Dodge next move\n4. Use Super"
                )
            elif first.can_super and second.spawn:
                moves = (
                    "1. Attack\n2. Try to collect gem\n3. Dodge next move"
                    f"\n4. Use Super\n5. Attack {second.spawn_str}"
                )
            elif not first.can_super and second.spawn:
                moves = (
                    "1. Attack\n2. Try to collect gem\n3. Dodge next move"
                    f"\n4. Attack enemy {second.spawn_str}"
                )
            else:
                moves = f"1. Attack\n2. Try to collect gem\n3. Dodge next move"
        else:
            if not second.spawn:
                moves = (
                    "1. Try to collect gem\n2. Dodge next move"
                    "\n3. Try to collect dropped gems"
                )
            else:
                moves = (
                    "1. Try to collect gem\n2. Dodge next move\n3. Try to "
                    f"collect dropped gems\n4. Attack enemy {second.spawn_str}"
                )

        return moves

    def gem_field(
        self,
        embed: discord.Embed,
        player: Player,
        opponent=False
    ):
        if opponent:
            iden = "Opponent's"
        else:
            iden = "Your"

        embed.add_field(
            name=f"{iden} Gems",
            value=f"{gamemode_emotes['Gem Grab']} {player.gems}"
            )

        return embed

    def set_embed_fields(
        self,
        embed: discord.Embed,
        player: Player,
        super_emote: str,
        opponent=False
    ):

        embed = self.initial_fields(embed, player, super_emote, opponent)
        embed = self.gem_field(embed, player, opponent)
        embed = self.spawn_field(embed, player, opponent)

        return embed

    def move_handler(
        self, choice: int, first: Player, second: Player, round_num: int
    ):

        if not second.is_respawning:
            if choice == 1:
                # attack
                self._move_attack(first, second, round_num)
            elif choice == 2:
                # collect gem
                self._move_gem(first, second)
            elif choice == 3:
                # invincibility
                self._move_invinc(first, second)
            elif choice == 4:
                if first.can_super:
                    # super
                    self._move_super(first, second, round_num)
                else:
                    # attack spawn
                    self._move_attack_spawn(first, second)
            elif choice == 5:
                # attack spawn
                self._move_attack_spawn(first, second)

            # spawn's attack
            self._move_spawn_attack(first, second)

        else:
            second.is_respawning = False
            if choice == 1:
                # collect gem
                self._move_gem(first, second)
            elif choice == 2:
                # invincibility
                self._move_invinc(first, second)
            elif choice == 3:
                # collect dropped gems
                self._move_dropped_gems(first, second)
            elif choice == 4:
                # attack spawn
                self._move_attack_spawn(first, second)

            # spawn's attack
            self._move_spawn_attack(first, second)

    def _move_gem(self, first: Player, second: Player):
        # 0.75 of collecting one gem
        collected_gem = random.choice([0, 1, 1, 1])
        first.gems += collected_gem
        if second.invincibility:
            second.invincibility = False

    def _move_dropped_gems(self, first: Player, second: Player):
        collected = random.randint(0, second.dropped)
        second.dropped = 0
        first.gems += collected
        if second.invincibility:
            second.invincibility = False


class Showdown(GameMode):
    """Class to represent Solo Showdown.

    It will be changed in the future to serve as a base for both Solo and Duo.
    """

    def __init__(self, ctx, user, opponent, conf, brawlers):
        super().__init__(ctx, user, opponent, conf, brawlers)

        self.poison_starting = 15
        self.poison_damage = 300

    async def initialize(self, ctx):
        first, second = await super().initialize(ctx)

        self.first.showdown()
        self.second.showdown()

        return first, second

    async def play(self, ctx: Context) -> (discord.User, discord.User):
        """Function to run the game"""

        i = 0
        while i < 100:
            # game ends after 50th round
            if i % 2 == 0:
                first = self.first
                second = self.second
            else:
                first = self.second
                second = self.first

            self.healing(i, first)

            try:
                await self.send_waiting_message(
                    ctx, first.player, second.player
                )
            except discord.Forbidden:
                raise

            if first.attacks >= 6:
                first.can_super = True
                end = 4
            else:
                first.can_super = False
                end = 3

            if second.spawn:
                if second.spawn > 0:
                    end += 1
                else:
                    second.spawn = None

            if first.player != self.guild.me:
                embed = await self.set_embed(ctx, first, second)
                try:
                    choice = await self.get_user_choice(
                        ctx, embed, end, first.player, second.player)
                except asyncio.TimeoutError:
                    winner, loser = second.player, first.player
                    break
            else:
                # develop bot logic
                choice = random.randint(1, end)

            self.move_handler(choice, first, second, i)

            # poison damage
            self.poison_effect(i)

            winner, loser = self.check_if_win(first, second)

            if winner is False:
                pass
            else:
                break
            # go to next loop
            i += 1

        # time up
        winner, loser = await self.time_up(winner, loser)

        await self.update_stats(winner, loser)

        return winner, loser

    def check_if_win(self, first: Player, second: Player):
        if first.health > 0 and second.health <= 0:
            winner = first.player
            loser = second.player
        elif second.health > 0 and first.health <= 0:
            winner = second.player
            loser = first.player
        elif second.health <= 0 and first.health <= 0:
            # draw
            winner = None
            loser = None
        else:
            # continues game
            winner = False
            loser = False

        return winner, loser

    async def set_embed(self, ctx: Context, first: Player, second: Player):
        if first.can_super:
            self_super_emote = emojis['superready']
        else:
            self_super_emote = emojis['supernotready']

        if second.can_super:
            opp_super_emote = emojis['superready']
        else:
            opp_super_emote = emojis['supernotready']

        embed = discord.Embed(
            color=EMBED_COLOR,
            title=f"Brawl against {second.player.name}"
        )
        embed.set_author(
            name=first.player.name, icon_url=first.player.avatar_url
        )

        embed = self.set_embed_fields(embed, first, self_super_emote, False)

        embed = self.set_embed_fields(embed, second, opp_super_emote, True)

        moves = self.moves_str(first, second)

        embed.add_field(name="Available Moves", value=moves, inline=False)

        return embed

    def moves_str(self, first: Player, second: Player):
        if first.can_super and not second.spawn:
            moves = (
                "1. Attack\n2. Try to collect powerup\n"
                "3. Dodge next move\n4. Use Super"
            )
        elif first.can_super and second.spawn:
            moves = (
                "1. Attack\n2. Try to collect powerup\n3. Dodge next move"
                f"\n4. Use Super\n5. Attack {second.spawn_str}"
            )
        elif not first.can_super and second.spawn:
            moves = (
                "1. Attack\n2. Try to collect powerup\n3. Dodge next move"
                f"\n4. Attack enemy {second.spawn_str}"
            )
        else:
            moves = (
                "1. Attack\n2. Try to collect powerup\n3. Dodge next move"
            )

        return moves

    def powerups_field(
        self,
        embed: discord.Embed,
        player: Player,
        opponent=False
    ):
        if opponent:
            iden = "Opponent's"
        else:
            iden = "Your"

        embed.add_field(
            name=f"{iden} Powerups",
            value=f"{emojis['powercube']} {player.powerups}"
            )

        return embed

    def set_embed_fields(
        self,
        embed: discord.Embed,
        player: Player,
        super_emote: str,
        opponent=False
    ):
        embed = self.initial_fields(embed, player, super_emote, opponent)
        embed = self.powerups_field(embed, player, opponent)
        embed = self.spawn_field(embed, player, opponent)

        return embed

    def move_handler(
        self, choice: int, first: Player, second: Player, round_num: int
    ):
        if not second.is_respawning:
            if choice == 1:
                # attack
                self._move_attack(first, second, round_num)
            elif choice == 2:
                # collect powerup
                self._move_powerup(first, second, round_num)
            elif choice == 3:
                # invincibility
                self._move_invinc(first, second)
            elif choice == 4:
                if first.can_super:
                    # super
                    self._move_super(first, second, round_num)
                else:
                    # attack spawn
                    self._move_attack_spawn(first, second)
            elif choice == 5:
                # attack spawn
                self._move_attack_spawn(first, second)

            # spawn's attack
            self._move_spawn_attack(first, second)

    def _move_powerup(self, first: Player, second: Player, round_num: int):
        first.last_attack = round_num

        # 0.5 of collecting powerup
        collected_powerup = random.choice([0, 1])
        first.powerups += collected_powerup
        if collected_powerup:
            self.buff_health(first)
        if second.invincibility:
            second.invincibility = False

    def buff_health(self, player: Player):
        player.static_health += 400
        player.health += 400

    def _move_attack(self, first: Player, second: Player, round_num: int):
        first.last_attack = round_num

        damage = self.apply_powerups(
            first, first.brawler._attack(first.brawler_level)
        )
        if not second.invincibility:
            second.health -= damage
            first.attacks += 1
        else:
            second.invincibility = False

    def _move_super(self, first: Player, second: Player, round_num: int):
        first.last_attack = round_num

        vals, first.spawn = first.brawler._ult(first.brawler_level)
        first.attacks = 0
        if isinstance(vals, list):
            # heal
            first.health += self.apply_powerups(first, vals[0])
            if first.health > first.static_health:
                first.health = first.static_health

            # hardcoding for Mortis to both
            # deal damage and heal
            vals = vals[0]
            if first.brawler_name != "Mortis":
                return

        if not second.invincibility:
            second.health -= self.apply_powerups(first, vals)
        else:
            second.health -= (self.apply_powerups(first, vals) * 0.5)
            second.invincibility = False

    def _move_attack_spawn(self, first: Player, second: Player):
        second.spawn -= self.apply_powerups(
            first, first.brawler._attack(first.brawler_level)
        )

    def _move_spawn_attack(self, first: Player, second: Player):
        if first.spawn:
            vals = first.brawler._spawn(first.brawler_level)
            if isinstance(vals, list):
                # heal
                first.health += self.apply_powerups(first, vals[0])
                if first.health > first.static_health:
                    first.health = first.static_health
            else:
                if not second.invincibility:
                    second.health -= self.apply_powerups(first, vals)
                    first.attacks += 1
                else:
                    second.invincibility = False

    def apply_powerups(self, player: Player, value: int):
        # 10% increase per powerup
        for _ in range(1, player.powerups):
            value += round(value * 0.1)

        return value

    def poison_effect(self, round_num: int):
        if round_num > self.poison_starting:
            self.first.health -= self.poison_damage
            self.second.health -= self.poison_damage


gamemodes_map = {
    "Gem Grab": GemGrab,
    "Solo Showdown": Showdown
}
