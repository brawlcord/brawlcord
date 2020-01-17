from collections import namedtuple

import discord

from discord.ext.commands.bot import Bot

from redbot.core import commands
from redbot.core.commands.context import Context
from redbot.core.bot import RedBase
from redbot.core.commands.help import RedHelpFormatter
from redbot.core.utils.chat_formatting import box, pagify


EmbedField = namedtuple("EmbedField", "name value inline")
EMPTY_STRING = "\N{ZERO WIDTH SPACE}"
INVITE_URL = ("https://discordapp.com/api/oauth2/authorize?client_id=644118957917208576"
    "&permissions=314432&scope=bot")
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

        description = ("Play a simple version of Brawl Stars on Discord. Use `-tutorial`"
            " command to begin.")
        tagline = f"Type {ctx.clean_prefix}help <command> for more info on a command. "
        
        coms = await self.get_bot_help_mapping(ctx)
        if not coms:
            return
        
        if await ctx.embed_requested():
            emb = {"embed": {"title": "", "description": description}, 
                "footer": {"text": ""}, "fields": []}
            
            # do not change 
            emb["embed"]["title"] = "***Red V3***"
            emb["footer"]["text"] = tagline

            general_str = ""
            general_cmd = ["brawl", "profile", "brawler", "brawlers", "allbrawlers",
                "stats", "gamemodes", "upgrade", "upgrades", "powerpoints"]
            rewards_str = ""
            rewards_cmd = ["brawlbox", "bigbox", "claim", "rewards", "gift"]
            misc_str = ""
            misc_cmd = ["leaderboard", "tutorial", "select", "brawlcord", "report", "invite"]
            red_cmd = ["info", "licenseinfo"]

            # commands = sorted(ctx.bot.commands, key=lambda x: x.name)

            titles = ["General", "Rewards", "Miscellaneous", "Red"]
            
            for title in titles:
                cog_text = ""
                for cog_name, data in coms:
                    for name, command in sorted(data.items()):
                        def add_com():
                            def shorten_line(a_line: str) -> str:
                                if len(a_line) < 70:  # embed max width needs to be lower than 70
                                    return a_line
                                return a_line[:67] + "..."

                            return (
                                "\n" + 
                                shorten_line(f"**{ctx.clean_prefix}{name}:** {command.short_doc}")
                            )

                        if title == titles[0]:
                            if name in general_cmd:
                                cog_text += add_com()
                        elif title == titles[1]:
                            if name in rewards_cmd:
                                cog_text += add_com()
                        elif title == titles[2]:
                            if name in misc_cmd:
                                cog_text += add_com()
                        elif title == titles[3]:
                            if name in red_cmd:
                                cog_text += add_com()
                        else:
                            continue
                
                for i, page in enumerate(pagify(cog_text, page_length=1000, shorten_by=0)):
                    title = f"__{title}:__" if i < 1 else f"__{title}:__ (continued)"
                    field = EmbedField(title, page, False)
                    emb["fields"].append(field)
                
            await self.make_and_send_embeds(ctx, emb)       
    
        else:
            return await ctx.send("Brawlcord requires the use of embeds. Please enable them!")

    async def make_and_send_embeds(self, ctx: Context, embed_dict: dict):

        pages = []

        help_settings = await commands.help.HelpSettings.from_context(ctx)
        
        page_char_limit = help_settings.page_char_limit

        field_groups = self.group_embed_fields(embed_dict["fields"], page_char_limit)

        page_count = len(field_groups)

        author_info = {"name": f"{ctx.me.display_name} Help Menu", "icon_url": ctx.me.avatar_url}

        if not field_groups:  # This can happen on single command without a docstring
            embed = discord.Embed(color=EMBED_COLOR, **embed_dict["embed"])
            embed.set_author(**author_info)
            embed.set_footer(**embed_dict["footer"])
            pages.append(embed)

        for i, group in enumerate(field_groups, 1):
            embed = discord.Embed(color=EMBED_COLOR, **embed_dict["embed"])

            if page_count > 1:
                description = f"{embed.description} *Page {i} of {page_count}*"
                embed.description = description

            embed.set_author(**author_info)

            for field in group:
                embed.add_field(**field._asdict())

            embed.set_footer(**embed_dict["footer"])

            pages.append(embed)

        await self.send_pages(ctx, pages, embed=True) 
