import asyncio
import logging
from datetime import datetime
from math import ceil

import discord

from .abc import MixinMeta

log = logging.getLogger("red.brawlcord.tasks")


class TasksMixin(MixinMeta):
    """Class for tasks."""

    async def update_token_bank(self):
        """Task to update token banks."""

        while True:
            for user in await self.config.all_users():
                user = self.bot.get_user(user)
                if not user:
                    continue
                tokens_in_bank = await self.get_player_stat(
                    user, 'tokens_in_bank')
                if tokens_in_bank == 200:
                    continue
                tokens_in_bank += 20
                if tokens_in_bank > 200:
                    tokens_in_bank = 200

                bank_update_timestamp = await self.get_player_stat(user, 'bank_update_ts')

                if not bank_update_timestamp:
                    continue

                bank_update_ts = datetime.utcfromtimestamp(ceil(bank_update_timestamp))
                time_now = datetime.utcnow()
                delta = time_now - bank_update_ts
                delta_min = delta.total_seconds() / 60

                if delta_min >= 80:
                    await self.update_player_stat(
                        user, 'tokens_in_bank', tokens_in_bank)
                    epoch = datetime(1970, 1, 1)

                    # get timestamp in UTC
                    timestamp = (time_now - epoch).total_seconds()
                    await self.update_player_stat(
                        user, 'bank_update_ts', timestamp)

            await asyncio.sleep(60)

    async def update_status(self):
        """Task to update bot's status with total guilds.

        Runs every 2 minutes.
        """

        while True:
            try:
                await self.bot.change_presence(
                    activity=discord.Game(
                        name=f'Brawl Stars in {len(self.bot.guilds)} servers'
                    )
                )
            except Exception:
                pass

            await asyncio.sleep(120)

    async def update_shop_and_st(self):
        """Task to update daily shop and star tokens."""

        while True:
            s_reset = await self.config.shop_reset_ts()
            create_shop = False
            if not s_reset:
                # first reset
                create_shop = True
            shop_diff = datetime.utcnow() - datetime.utcfromtimestamp(s_reset)

            st_reset = await self.config.st_reset_ts()
            reset = False
            if not st_reset:
                # first reset
                reset = True
                continue
            st_diff = datetime.utcnow() - datetime.utcfromtimestamp(st_reset)

            for user in await self.config.all_users():
                user = self.bot.get_user(user)
                if not user:
                    continue
                if create_shop:
                    await self.create_shop(user)
                    continue
                if shop_diff.days > 0:
                    await self.create_shop(user)

                st_reset = await self.config.st_reset_ts()
                if reset:
                    await self.reset_st(user)
                    continue
                if st_diff.days > 0:
                    await self.reset_st(user)

            await asyncio.sleep(300)
