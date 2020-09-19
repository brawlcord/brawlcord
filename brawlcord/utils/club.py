import random
import string
from typing import Callable, List, Optional

import discord
from redbot.core import Config
from redbot.core.commands import Context
from redbot.core.bot import Red
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
# from redbot.core.utils.chat_formatting import text_to_file

from .constants import EMBED_COLOR
from .emojis import emojis
from .errors import CancellationError

# Credits to Star List
club_thumb = "https://www.starlist.pro/assets/club/{}.png"


class Club:
    """Represents a Brawlcord club."""

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.required_trophies: int = data["required_trophies"]
        self.location: str = data["location"]
        self.icon_num: int = data["icon_num"]
        self.ctype: str = data["ctype"]
        self.president: discord.User = data["president"]

        self.vice_presidents: List[discord.User] = data.get("vice_presidents", [])
        self.seniors: List[discord.User] = data.get("seniors", [])
        self.members: List[discord.User] = data.get("members", [])

        self.all_members = [self.president] + self.vice_presidents + self.seniors + self.members

    @classmethod
    async def create_club(cls, config: Config, ctx: Context):
        """Interactive club creation process.

        This function creates the club, adds it to both user and global database
        and returns the club object. It also adjusts the `club_id_length` if required.

        All errors must be handled in the caller function.
        """

        async def get_input(timeout=30):
            pred = await ctx.bot.wait_for(
                "message", check=MessagePredicate.same_context(ctx), timeout=timeout
            )
            if pred.content.strip().lower() == "cancel":
                raise CancellationError

            return pred.content.strip()

        data = {}

        await ctx.send(
            ":tada: Let's create your club! First, what name do you want the club to have?"
            " Note that it cannot be changed later!"
        )
        data["name"] = await get_input()

        await ctx.send(
            "Set the name! Now, what do you want to set as the server description?"
        )
        data["description"] = await get_input(60)

        await ctx.send(
            "Set the description! What should be the required trophies?"
            " Enter a number. (without commas)"
        )
        data["required_trophies"] = int(await get_input())

        await ctx.send(
            "Set required trophies! Select a icon for the club!"
            " Enter the number corresponding to icon of choice."
        )
        data["icon_num"] = int(await get_input(60))

        await ctx.send(
            "Set club icon! Now, enter a location for your club!"
        )
        data["location"] = await get_input()

        await ctx.send(
            "Set the location. Lastly, what kind of club do you want to create?"
            " Enter one of `open`, `closed`, or `invite`."
        )
        club_type = await get_input()
        if club_type.strip().lower() not in ["open", "closed", "invite"]:
            # We raise `NameError` instead of `ValueError` to keep
            # it separate from the above `int` conversions.
            raise NameError
        else:
            data["ctype"] = club_type

        data["president"] = ctx.author

        await ctx.send(
            f"All set! Club created! :tada:")

        default_length = await config.club_id_length()
        async with config.clubs() as clubs:
            # First we get all club IDs we've used so far to get an ID for our new club.
            ids = [c["id"] for c in clubs]
            data["id"], new_length = cls.get_club_id(ids, default_length)
            club = cls(data)
            clubs.append(club.to_json())

        await config.user(ctx.author).club.set(club.id)

        if default_length != new_length:
            await config.club_id_length.set(new_length)

        return club

    def to_json(self) -> dict:
        """Returns a dictionary represeting the `Club` object."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_trophies": self.required_trophies,
            "location": self.location,
            "icon_num": self.icon_num,
            "ctype": self.ctype,
            "president_id": self.president.id,
            "vice_president_ids": [vp.id for vp in self.vice_presidents],
            "senior_ids": [s.id for s in self.seniors],
            "member_ids": [m.id for m in self.members]
        }

    @classmethod
    async def from_json(cls, data: dict, bot: Red):
        """Return a `Club` object from dictionary representation of the club."""

        data["president"] = await cls.get_user(data["president_id"], bot)

        vice_presidents = []
        for vp_id in data["vice_president_ids"]:
            vp = await cls.get_user(vp_id, bot)
            if vp is not None:
                vice_presidents.append(vp)
        data["vice_presidents"] = vice_presidents

        seniors = []
        for s_id in data["senior_ids"]:
            sen = await cls.get_user(s_id, bot)
            if sen is not None:
                seniors.append(sen)
        data["seniors"] = seniors

        members = []
        for m_id in data["member_ids"]:
            mem = await cls.get_user(m_id, bot)
            if mem is not None:
                members.append(mem)
        data["members"] = members

        data.pop("president_id")
        data.pop("vice_president_ids")
        data.pop("senior_ids")
        data.pop("member_ids")

        return cls(data)

    @staticmethod
    async def get_user(user_id: int, bot: Red) -> Optional[discord.User]:
        """Returns `discord.User` object from the given ID.

        Returns `None` if user can't be found.
        """

        user = bot.get_user(user_id)
        if user is None:
            try:
                user = await bot.fetch_user(user_id)
            except Exception:
                pass
        return user

    @staticmethod
    async def show_club(
        data: dict, bot: Red, config: Config, get_league: Callable
    ) -> (discord.Embed, discord.File):
        """Returns a tuple of length two.

        First element is a formatted `discord.Embed` object to display the club.
        Second is a `discord.File` with data about all club members. It is `None`
        is club has less than or equal to 10 members.
        """

        if isinstance(data, Club):
            club = data
        else:
            club: Club = await Club.from_json(data, bot)

        embeds = []
        pages = await club.members_list(config, get_league)
        total_pages = len(pages)
        total_trophies = await club.total_trophies(config)
        if club.icon_num not in range(1, 31):
            icon_url = "https://www.starlist.pro/assets/icon/Club.png"
        else:
            icon_url = club_thumb.format(club.icon_num - 1)

        for idx, page in enumerate(pages):
            # if not page.strip():
            #     continue
            embed = discord.Embed(color=EMBED_COLOR, description=club.description)

            # Star List's club indexing starts a 0, ours at 1.
            # It goes all the way up till 29.
            embed.set_author(name=club.name, icon_url=icon_url)
            embed.set_footer(text=f"Club ID: {club.id} | Page {idx+1}/{total_pages}")

            embed.add_field(
                name="Total Trophies",
                value=f"{emojis['trophies']} {total_trophies:,}"
            )
            embed.add_field(name="President", value=club.president.name)
            embed.add_field(
                name="Required Trophies", value=f"{emojis['trophies']} {club.required_trophies:,}"
            )
            embed.add_field(name="Total Members", value=f"{len(club.all_members)}/100")
            embed.add_field(name="Type", value=club.ctype.title())
            embed.add_field(name="Location", value=club.location)

            embed.add_field(name="\u200b\n", value=page.strip(), inline=False)

            embeds.append(embed)
        # if whole:
        #     club_file = text_to_file(whole, "club_data.txt")
        # else:
        #     club_file = None

        return embeds

    async def total_trophies(self, config: Config) -> int:
        """Returns total club trophies."""

        total = 0

        for member in self.all_members:
            try:
                brawlers = await config.user(member).brawlers()
                total += self.get_user_trophies(brawlers)
            except Exception:
                continue

        return total

    @staticmethod
    def get_user_trophies(brawlers: dict) -> int:
        """Returns total trophies of the user."""

        return sum([brawlers[brawler]["trophies"] for brawler in brawlers])

    async def members_list(self, config: Config, get_league: Callable) -> (str, str):
        """Returns a tuple of two strings.

        First string is for top ten club members (in terms of trophies).
        Second is for all. If the club has less than or equal to 10 members,
        the second string is empty.
        """

        mapping = {}

        for member in self.all_members:
            try:
                brawlers = await config.user(member).brawlers()
                mapping[member] = self.get_user_trophies(brawlers)
            except Exception:
                pass

        # Sort mapping to get users with most trophies at the top.
        mapping = {k: v for k, v in sorted(mapping.items(), key=lambda x: x[1], reverse=True)}
        # total_num = len(mapping)

        first_ten_txt = ""
        second_ten_txt = ""
        third_ten_txt = ""
        fourth_ten_txt = ""
        fifth_ten_txt = ""
        # whole_txt = ""

        for idx, user in enumerate(mapping):
            pos = "Member"

            if user.id == self.president.id:
                pos = "**President**"
            elif user.id in [vp.id for vp in self.vice_presidents]:
                pos = "**Vice President**"
            elif user.id in [s.id for s in self.seniors]:
                pos = "**Senior**"

            _, emoji = await get_league(mapping[user])
            txt = f"\n`{(idx+1):02d}.` {user} {emoji}{mapping[user]} ({pos})"

            if idx in range(0, 10):
                first_ten_txt += txt
            if idx in range(10, 20):
                second_ten_txt += txt
            if idx in range(20, 30):
                third_ten_txt += txt
            if idx in range(30, 40):
                fourth_ten_txt += txt
            if idx in range(40, 50):
                fifth_ten_txt += txt

        pages = [
            page for page in
                [first_ten_txt, second_ten_txt, third_ten_txt, fourth_ten_txt, fifth_ten_txt]
            if page.strip()
        ]
        return pages

    @staticmethod
    def get_club_id(used_ids: list, default_length: int) -> (str, int):
        """Returns a unique id for the club and the default length we should use."""

        def gen_id(length=default_length):
            id = "".join(
                [random.choice(string.ascii_uppercase + string.digits) for _ in range(length)]
            )
            if id not in used_ids:
                return id
            else:
                return False

        id = gen_id()
        if id is False:
            # If id is not unique, try generating id of default length 3 more times.
            # Increase length by one if still not unique.
            for _ in range(3):
                id = gen_id()
                if id is False:
                    continue
                else:
                    return id
            default_length += 1
            id = gen_id(default_length)

        return id, default_length

    @classmethod
    async def club_from_id(cls, id: str, config: Config, bot: Red):
        """Returns `Club` instance representing club with given id.

        Returns `None` if club with given id doesn't exist.
        """

        clubs = await config.clubs()
        for club in clubs:
            if club["id"] == id:
                return await cls.from_json(club, bot)

    async def remove_user(self, user: discord.User, config: Config):
        """Removes user from club lists."""

        def choose_new_pres(pool: list):
            try:
                new_pres = random.choice(pool)
                # Remove it from pool.
                pool.remove(new_pres)
                # Set it as new president.
                self.president = new_pres
                return True
            except IndexError:
                return False

        if user in self.all_members:
            self.all_members.remove(user)

        if user.id == self.president.id:
            if not choose_new_pres(self.vice_presidents):
                if not choose_new_pres(self.seniors):
                    if not choose_new_pres(self.members):
                        # Empty club, remove it from database.
                        async with config.clubs() as clubs:
                            where = next(i for i, d in enumerate(clubs) if d.get('id') == self.id)
                            del clubs[where]
                            return True
        else:
            if user in self.vice_presidents:
                self.vice_presidents.remove(user)
            elif user in self.seniors:
                self.seniors.remove(user)
            elif user in self.members:
                self.members.remove(user)

        await self.update_club(config)

    async def add_user(self, user: discord.User, config: Config):
        """Adds users to the club list."""

        if self.ctype in ["closed", "invite"]:
            raise ValueError("Club type is `closed` or `invite-only`.")

        self.members.append(user)

        await self.update_club(config)

    async def promote_user(self, user: discord.User, ctx: Context, config: Config):
        """Promotes a user.

        Raises ValueError if not allowed.
        """

        if user.id == self.president.id:
            raise ValueError(f"{user.name} is the club President!")

        if ctx.author.id == self.president.id:
            if user in self.vice_presidents:
                msg = await ctx.send(
                    f"Promoting {user.name} will demote you and make them the President."
                    " Are you sure you want to continue?"
                )
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                await ctx.bot.wait_for("reaction_add", check=pred)

                if pred.result is True:
                    self.president = user
                    self.vice_presidents.remove(user)
                    self.vice_presidents.append(ctx.author)
                    await ctx.send(f"Promoted {user.name} to President!")
                else:
                    return await ctx.send("Cancelled promotion.")
            elif user in self.seniors:
                self.seniors.remove(user)
                self.vice_presidents.append(user)
                await ctx.send(f"Promoted {user.name} to Vice President!")
            elif user in self.members:
                self.members.remove(user)
                self.seniors.append(user)
                await ctx.send(f"Promoted {user.name} to Senior!")

        if ctx.author in self.vice_presidents:
            if user in self.vice_presidents:
                raise ValueError(f"{user.name} is equal to you in hierarchy!")
            elif user in self.seniors:
                raise ValueError(f"Only club President can promote a Senior to Vice President")
            elif user in self.members:
                self.members.remove(user)
                self.seniors.append(user)
                await ctx.send(f"Promoted {user.name} to Senior!")

        await self.update_club(config)

    async def demote_user(self, user: discord.User, ctx: Context, config: Config):
        """Demotes a user.

        Raises ValueError if not allowed.
        """

        if user.id == self.president.id:
            raise ValueError(f"{user.name} is the club President!")

        if ctx.author.id == self.president.id:
            if user in self.vice_presidents:
                self.vice_presidents.remove(user)
                await ctx.send(f"Demoted {user.name} to Senior!")
            elif user in self.seniors:
                self.seniors.remove(user)
                await ctx.send(f"Demoted {user.name} to Member!")
            elif user in self.members:
                raise ValueError(
                    f"{user.name} is already a Member."
                    " Use `club kick` command to kick member out of the club."
                )

        if ctx.author in self.vice_presidents:
            if user in self.vice_presidents:
                raise ValueError(f"{user.name} is equal to you in hierarchy!")
            elif user in self.seniors:
                self.seniors.remove(user)
                await ctx.send(f"Demoted {user.name} to Member!")
            elif user in self.members:
                raise ValueError(
                    f"{user.name} is already a Member."
                    " Use `club kick` command to kick member out of the club."
                )

        await self.update_club(config)

    async def update_club(self, config: Config):
        """Updates club in the bot database."""

        async with config.clubs() as clubs:
            where = next(i for i, d in enumerate(clubs) if d.get('id') == self.id)
            clubs[where] = self.to_json()
            return True
