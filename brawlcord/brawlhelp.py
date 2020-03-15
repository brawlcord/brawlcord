from collections import namedtuple

from redbot.core.commands.context import Context
from redbot.core.commands.help import RedHelpFormatter
from redbot.core.utils.chat_formatting import pagify

EmbedField = namedtuple("EmbedField", "name value inline")
EMPTY_STRING = "\N{ZERO WIDTH SPACE}"
INVITE_URL = (
    "https://discordapp.com/api/oauth2/authorize?client_id="
    "644118957917208576&permissions=321600&scope=bot"
)
SELF_EMOTE = "<:Brawlcord:648245740409323600>"
DISCORD_EMOTE = "<:discord:648246368539901961>"
GITHUB_LINK = "https://snowsee.github.io/brawlcord/"
SOURCE_LINK = "https://github.com/snowsee/brawlcord"
COMMUNITY_LINK = GITHUB_LINK + "#how-to-use"
REDDIT_LINK = "https://www.reddit.com/user/Snowsee"
EMBED_COLOR = 0xFFA232


class BrawlcordHelp(RedHelpFormatter):
    """
    Brawlcord's help implementation.

    Lists all commands and their descriptions in custom categories.

    Also includes necessary Red mentions and commands.
    """

    def __init__(self, bot):
        self.bot = bot

    async def format_bot_help(self, ctx: Context):
        """Format the default help message"""

        tagline = (
            f"Type {ctx.clean_prefix}help <command>"
            " for more info on a command."
        )

        coms = await self.get_bot_help_mapping(ctx)
        if not coms:
            return

        if await ctx.embed_requested():
            emb = {
                "embed": {"title": "", "description": ""},
                "footer": {"text": ""}, "fields": []
            }

            # do not change
            # emb["embed"]["title"] = "Brawlcord"
            emb["footer"]["text"] = tagline

            general_cmd = [
                "brawl", "profile", "brawler", "brawlers", "allbrawlers",
                "stats", "gamemodes", "upgrade", "upgrades", "powerpoints"
            ]
            rewards_cmd = ["brawlbox", "bigbox", "claim", "rewards", "gift"]

            utility_cmd = [
                "leaderboard", "tutorial", "select", "brawlcord",
                "report", "invite", "skins", "startokens"
            ]

            misc_cmd = ["setprefix", "info", "licenseinfo"]

            # commands = sorted(ctx.bot.commands, key=lambda x: x.name)

            titles = ["General", "Rewards", "Utility", "Misc"]

            for title in titles:
                cog_text = ""
                for cog_name, data in coms:
                    for name, command in sorted(data.items()):
                        def add_com():
                            def shorten_line(a_line: str) -> str:
                                # embed max width needs to be lower than 70
                                if len(a_line) < 70:
                                    return a_line
                                return a_line[:67] + "..."

                            return (
                                "\n" +
                                shorten_line(
                                    f"**{ctx.clean_prefix}{name}:**"
                                    f" {command.short_doc}"
                                )
                            )

                        if title == titles[0]:
                            if name in general_cmd:
                                cog_text += add_com()
                        elif title == titles[1]:
                            if name in rewards_cmd:
                                cog_text += add_com()
                        elif title == titles[2]:
                            if name in utility_cmd:
                                cog_text += add_com()
                        elif title == titles[3]:
                            if name in misc_cmd:
                                cog_text += add_com()
                        else:
                            continue

                for i, page in enumerate(
                    pagify(cog_text, page_length=1000, shorten_by=0)
                ):
                    title = (
                        f"__{title}:__" if i < 1 else
                        f"__{title}:__ (continued)"
                    )
                    field = EmbedField(title, page, False)
                    emb["fields"].append(field)

            await self.make_and_send_embeds(ctx, emb)

        else:
            return await ctx.send(
                "Brawlcord requires the use"
                "of embeds. Please enable them!"
            )
