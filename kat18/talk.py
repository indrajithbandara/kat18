"""
Handles talking.
"""
import asyncio
import random


def talk_time(msg):
    """Formulae for calculating how long to type for."""
    return len(msg.content) * 0.01 + (random.random() * 2 + 1)


class Talk:
    """Handles talking."""
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        """Handles replying to users."""
        expected_prefix = f'{self.bot.name.lower()}:'

        # Return if we don't start with the prefix.
        if not message.content.lstrip().lower().startswith(expected_prefix):
            return

        # If the user is unauthorised, reply with an angry face.
        if message.author.id not in self.bot.commanders:
            await message.add_reaction('\N{ANGRY FACE}')
            return

        asyncio.ensure_future(message.delete())

        # Remove the prefix from the message content
        message.content = message.content[len(expected_prefix):].lstrip()

        async with message.channel.typing():
            await asyncio.sleep(talk_time(message))

            await message.channel.send(message.content)


def setup(bot):
    bot.add_cog(Talk(bot))
