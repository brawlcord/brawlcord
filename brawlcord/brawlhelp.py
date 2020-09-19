from collections import namedtuple

import discord
from redbot.core.commands.context import Context
from redbot.core.commands.help import HelpSettings, RedHelpFormatter
from redbot.core.utils.chat_formatting import pagify

from .utils.constants import COMMANDS_PAGE, COMMUNITY_SERVER

EmbedField = namedtuple("EmbedField", "name value inline")


class BrawlcordHelp(RedHelpFormatter):
    """Brawlcord's help implementation.

    Lists all commands and their descriptions in custom categories.

    Also includes necessary Red mentions and commands.
    """

    def __init__(self, bot):
        self.bot = bot

    async def format_bot_help(self, ctx: Context, help_settings: HelpSettings):
        """Format the default help message"""

        coms = await self.get_bot_help_mapping(ctx, help_settings)
        if not coms:
            return

        if not await ctx.embed_requested():
            return await ctx.send(
                "Brawlcord requires the use of embeds. Please enable them!"
            )

        tagline = self.get_default_tagline(ctx)

        emb = {
            "embed": {"title": "", "description": ""}, "footer": {"text": ""}, "fields": []
        }

        emb["embed"]["description"] = (
            f"You can also view the list of commands [here]({COMMANDS_PAGE})."
            " Feel free to suggest new features in"
            f" [the community server]({COMMUNITY_SERVER})."
        )
        emb["footer"]["text"] = tagline

        gameplay_cmds = [
            "brawl", "brawler", "tutorial", "allbrawlers", "gamemode",
            "gamemodes", "upgrade", "shop", "select", "battlelog", "club"
        ]
        stat_cmds = [
            "profile", "stats", "upgrades", "powerpoints", "skins",
            "startokens", "brawlers", "leaderboard", "drops"
        ]
        economy_cmds = ["brawlbox", "bigbox", "claim", "rewards", "gift"]
        misc_cmds = [
            "setprefix", "report", "invite", "info",
            "licenseinfo", "redinfo", "support", "discord",
            "license", "credits", "deletedata", "getdata"
        ]

        titles = ["Gameplay", "Statistics", "Economy", "Misc"]

        for title in titles:
            cog_text = ""
            for cog_name, data in coms:
                for name, command in sorted(data.items()):
                    def add_com():
                        command_info = f"**{ctx.clean_prefix}{name}** - {command.short_doc}"

                        if len(command_info) < 70:
                            return "\n" + command_info
                        return "\n" + command_info[:67] + "..."

                    if title == titles[0] and name in gameplay_cmds:
                        cog_text += add_com()
                    if title == titles[1] and name in stat_cmds:
                        cog_text += add_com()
                    elif title == titles[2] and name in economy_cmds:
                        cog_text += add_com()
                    elif title == titles[3] and name in misc_cmds:
                        cog_text += add_com()
                    else:
                        continue

            for i, page in enumerate(
                pagify(cog_text, page_length=1000, shorten_by=0)
            ):
                title = (
                    f"**{title}**" if i < 1 else
                    f"**{title} (continued)**"
                )
                field = EmbedField(title, page, False)
                emb["fields"].append(field)

        await self.make_and_send_embeds(ctx, emb, help_settings)

    async def make_and_send_embeds(self, ctx, embed_dict: dict, help_settings: HelpSettings):

        pages = []

        page_char_limit = 1000

        author_info = {
            "name": f"{ctx.me.display_name} Help",
            "icon_url": ctx.me.avatar_url,
        }

        # Offset calculation here is for total embed size limit
        # 20 accounts for# *Page {i} of {page_count}*
        offset = len(author_info["name"])  # + 20
        foot_text = embed_dict["footer"]["text"]
        if foot_text:
            offset += len(foot_text)
        offset += len(embed_dict["embed"]["description"])
        offset += len(embed_dict["embed"]["title"])

        # In order to only change the size of embeds when neccessary for this rather
        # than change the existing behavior for people uneffected by this
        # we're only modifying the page char limit should they be impacted.
        # We could consider changing this to always just subtract the offset,
        # But based on when this is being handled (very end of 3.2 release)
        # I'd rather not stick a major visual behavior change in at the last moment.
        if page_char_limit + offset > 5500:
            # This is still neccessary with the max interaction above
            # While we could subtract 100% of the time the offset from page_char_limit
            # the intent here is to shorten again
            # *only* when neccessary, by the exact neccessary amount
            # To retain a visual match with prior behavior.
            page_char_limit = 5500 - offset
        elif page_char_limit < 250:
            # Prevents an edge case where a combination of long cog help and low limit
            # Could prevent anything from ever showing up.
            # This lower bound is safe based on parts of embed in use.
            page_char_limit = 250

        field_groups = self.group_embed_fields(embed_dict["fields"], page_char_limit)

        color = await ctx.embed_color()
        page_count = len(field_groups)

        if not field_groups:  # This can happen on single command without a docstring
            embed = discord.Embed(color=color, **embed_dict["embed"])
            embed.set_author(**author_info)
            embed.set_footer(**embed_dict["footer"])
            pages.append(embed)

        for i, group in enumerate(field_groups, 1):
            embed = discord.Embed(color=color, **embed_dict["embed"])

            embed.set_author(**author_info)

            for field in group:
                embed.add_field(**field._asdict())

            embed.set_footer(**embed_dict["footer"])
            if page_count > 1:
                footer_text = f"Page {i} of {page_count} ◆ {embed.footer.text}"
                footer_icon_url = embed.footer.icon_url
                embed.set_footer(text=footer_text, icon_url=footer_icon_url)

            pages.append(embed)

        await self.send_pages(ctx, pages, embed=True, help_settings=help_settings)

    def get_default_tagline(self, ctx):
        return (
            f"Type {ctx.clean_prefix}help <command> for more info on a command."
        )
