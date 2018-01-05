"""
Utility classes and methods.
"""

import abc
import asyncio
import logging
import traceback

import discord
import discord.ext.commands as commands

__all__ = ['Loggable', 'KatCommand', 'command', 'group', 'confirm_operation']


class Loggable(abc.ABC):
    """
    Injects a logger into an implementing class.
    """
    __slots__ = ['logger']

    def __init_subclass__(cls, *_):
        cls.logger = logging.getLogger(cls.__name__)


class KatCommandMixin(abc.ABC):
    """
    Implements the "on_error" handler. This just returns a semi-friendly
    message if stuff messes up.
    """
    @staticmethod
    async def on_error(*args):
        if len(args) == 2:
            cog = None
            ctx, error = args
        else:
            cog, ctx, error = args

        if isinstance(error, commands.CheckFailure):
            msg = ('You don\'t have permission to do this to me! ' 
                   '\N{face with tears of joy}')
        else:
            msg = str(error.__cause__ if error.__cause__ else error)

        embed = discord.Embed(
            title='Uh-oh!',
            description=msg,
            color=0xFF0000
        )

        embed.set_footer(text=f'In cog {type(cog).__name__}.')

        await ctx.send(embed=embed)
        traceback.print_exception(type(error), error, error.__traceback__)


class KatCommand(commands.Command, KatCommandMixin):
    pass


class KatGroup(commands.Group, KatCommandMixin):
    def command(self, **kwargs):
        kwargs.setdefault('cls', KatCommand)
        return super().command(**kwargs)

    def group(self, **kwargs):
        kwargs.setdefault('cls', KatGroup)
        return self.command(**kwargs)


def command(**kwargs):
    """
    Like the discord.ext.commands one... except it defaults to the KatCommand
    class instead.
    """
    kwargs.setdefault('cls', KatCommand)
    return commands.command(**kwargs)


def group(**kwargs):
    """
    Like the discord.ext.commands one... except it defaults to the KatCommand
    class instead.
    """
    kwargs.setdefault('cls', KatGroup)
    return commands.command(**kwargs)


check = commands.check


def confirm_operation(ctx):
    """
    Confirms an operation's success by replying to a ctx and deleting
    after a few seconds.
    """
    async def coro():
        asyncio.ensure_future(ctx.message.add_reaction('\N{OK HAND SIGN}'))
        await asyncio.sleep(5)
        # noinspection PyBroadException
        try:
            await ctx.message.delete()
        except BaseException:
            pass
    asyncio.ensure_future(coro())


def make_closeable(ctx, msg):
    """
    Adds a reaction to the message and allows the ctx sender
    to close it. After a timeout the message will self
    destruct. This is all done as ensured futures so does
    not and should not be awaited.
    
    :param ctx: the original command invocation ctx.
    :param msg: the message to destroy.
    """
    # noInspection PyBroadException
    try:
        emote = '\N{REGIONAL INDICATOR SYMBOL LETTER X}'
        asyncio.ensure_future(msg.add_reaction(emote))

        async def callback():
            nonlocal emote
            nonlocal ctx
            nonlocal msg
            try:
                await ctx.bot.wait_for(
                    'reaction_add',
                    timeout=60,
                    check=lambda r, u: u.id == ctx.author.id
                                       and r.message.id == msg.id
                                       and r.emoji == emote
                )
            except asyncio.TimeoutError:
                pass
            finally:
                asyncio.ensure_future(msg.delete())
        asyncio.ensure_future(callback())
    except BaseException:
        pass
