from .brawlcord import Brawlcord


async def setup(bot):
    cog = Brawlcord(bot)
    await cog.initialize()
    bot.add_cog(cog)
