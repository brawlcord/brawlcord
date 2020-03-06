from .brawlcord import Brawlcord


async def setup(bot):
    old_invite = bot.get_command("invite")
    if old_invite:
        bot.remove_command(old_invite.name)
    cog = Brawlcord(bot)
    await cog.initialize()
    bot.add_cog(cog)
