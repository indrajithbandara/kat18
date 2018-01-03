import asyncio
import random

import discord


class Reacting:
    """Reacts to messages containing certain words or patterns"""
    def __init__(self, bot):
        self.bot = bot
        self.buckets = 0

    async def on_message(self, message):
        # Do not run in DMs, if we are on timeout, or if the author is a bot.
        if not message.guild or self.buckets > 0 or message.author.bot:
            return

        contains_pattern = False

        for pattern in self.bot.patterns:
            if pattern.match(message.content):
                contains_pattern = True
                break

        if not contains_pattern:
            return

        # Get a random emoji, if we have any.
        emojis = self.bot.loaded_emojis

        blacklist = self.bot.dont_react_in.get()
        c_id = message.channel.id
        g_id = message.guild.id

        chan_match = discord.utils.find(
            lambda c: c == c_id,
            blacklist.get(str(g_id), {})
        )

        if chan_match:
            # We are in a blacklisted channel/server. Skip.
            self.bot.logger.info('Not reacting. Blacklisted channel.')
            return

        # If we have no emojis, or in 50% of cases anyway; then skip.
        if len(emojis) == 0 or random.random() > 0.5:
            return

        emoji = random.choice(emojis)

        async def react():
            """Reacts at some point in the next 30 seconds."""
            await asyncio.sleep(random.randint(0, 30))
            await message.add_reaction(emoji)

        asyncio.ensure_future(react())
        asyncio.ensure_future(self.timeout())

    async def timeout(self):
        self.buckets += 1
        # Timeout of 5 minutes
        await asyncio.sleep(5 * 60)
        self.buckets -= 1


def setup(bot):
    bot.add_cog(Reacting(bot))
