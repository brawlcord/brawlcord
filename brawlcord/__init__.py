from .brawlcord import BrawlCord


async def setup(bot):
    cog = BrawlCord(bot)
    await cog.initialize()
    bot.add_cog(cog)
