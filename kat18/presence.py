"""
Handles the bot presence, game, etc.
"""
import discord

import kat18.util as util


class Presence:
    """Handles setting the bot presence and the bot's game."""
    def __init__(self, bot):
        self.bot = bot
        self.default_game = None

        # Dpy doesn't seem to provide any way of getting these,
        # and the behaviour of change_presence means all values have to
        # be respecified otherwise they get reset!
        self.game = None
        self.status = None

    async def on_ready(self):
        bot_mention = f'@{self.bot.user.name}'
        self.default_game = discord.Game(name=f'say {bot_mention} help')
        await self.bot.change_presence(game=self.default_game)
        self.game = self.default_game

    @util.command(
        name='status',
        brief='Set my bot presence.',
        usage='available|online|away|idle|dnd|do not disturb|invisible|offline'
    )
    async def set_status(self, ctx, *, status):
        """
        Sets the bot presence.

        Valid options:

        - available, online: Online (green)
        - away, idle: Idle (amber)
        - dnd, do not disturb: Do Not Disturb (red)
        - invisible, offline: Invisible (grey)
        """
        status = status.strip().lower()
        presence_map = {
            'available': discord.Status.online,
            'online': discord.Status.online,
            'away': discord.Status.idle,
            'idle': discord.Status.idle,
            'dnd': discord.Status.dnd,
            'do not disturb': discord.Status.dnd,
            'invisible': discord.Status.invisible,
            'offline': discord.Status.invisible
        }

        status_obj = presence_map.get(status.lower())

        if status_obj is None:
            raise ValueError(f'{status} is not a valid status. Read the help!')

        await self.bot.change_presence(status=status_obj, game=self.game)
        self.status = status_obj
        util.confirm_operation(ctx)

    @util.command(
        name='game',
        brief='Sets the game I am playing.',
        usage='name'
    )
    async def set_game(self, ctx, *, name=None):
        """
        Sets the game I am playing.

        If you don't specify a game, I will default to my default message.
        """
        game = self.default_game if name is None else discord.Game(name=name)

        await self.bot.change_presence(
            game=game,
            status=self.status)

        self.game = game

        util.confirm_operation(ctx)


def setup(bot):
    bot.add_cog(Presence(bot))
