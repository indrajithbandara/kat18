"""
Class that implements the Bot class.
"""
import copy
import json
import os
import re

import asyncio

import discord.utils as dutils
import discord.ext.commands as commands

import kat18.aio as asyncjson
import kat18.util as util


extensions = {
    'kat18.talk',
    'kat18.presence',
    'kat18.admin'
}


class KatBot(commands.Bot, util.Loggable):
    """Kat bot client."""

    def __init__(self, config_location):
        """
        Init the client.

        :param config_location:
        """
        self.config_location = config_location

        with open(os.path.join(config_location, 'config.json')) as fp:
            config: dict = json.load(fp)

        self.config = config

        super().__init__(command_prefix=commands.when_mentioned,
                         owner_id=config['owner_id'])

        self.logger.info(f'Add me to a guild at: {self.invite}')

        self.commanders = asyncjson.AsyncJsonValue(
            os.path.join(config_location, 'authorized_commanders.json'),
            []
        )

        if self.owner_id not in self.commanders.cached_value:
            new_list = self.commanders.get()
            new_list.append(self.owner_id)
            asyncio.wait(asyncio.gather(self.commanders.set(new_list)))

        # We write a wrapper around this.
        self._loaded_emojis_raw = asyncjson.AsyncJsonValue(
            os.path.join(config_location, 'react_emojis.json'),
            []
        )

        # On any chance that emojis that are available change, we recache
        # the entire list asynchronously.
        # Don't do it on_ready, as when guilds become available, they should
        # trigger this event anyway.
        # @self.listen('on_ready')
        @self.listen('on_guild_join')
        @self.listen('on_guild_available')
        @self.listen('on_guild_unavailable')
        @self.listen('on_guild_emojis_update')
        async def re_cache_emojis(*_, **__):
            self.logger.info('Some event has triggered an emoji recache...')
            await self.reload_emoji_cache()
            emoji_count = len(self._loaded_emoji_cache)
            self.logger.info(
                f'Recaching has finished. I have {emoji_count} emojis'
            )

        self._loaded_emoji_cache = []

        # We write a wrapper around this.
        self._patterns_raw = asyncjson.AsyncJsonValue(
            os.path.join(config_location, 'react_triggers.json'),
            ['Kat']
        )

        # Load the pattern cache
        asyncio.wait(asyncio.gather(self.recompile_patterns()))

        self._patterns_cache = []

        # Load the cogs.
        for ext in extensions:
            self.load_extension(ext)

    @property
    def invite(self):
        """Gets a bot invite link."""
        return ('https://discordapp.com/oauth2/authorize?scope=bot'
                f'&client_id={self.client_id}')

    @property
    def client_id(self):
        """Gets the bot client id."""
        return self.config['client_id']

    @property
    def __token(self):
        """Gets the bot token."""
        return self.config['token']

    @property
    def name(self):
        """Gets the bot name."""
        return self.config['name']

    def run(self):
        """Runs the bot."""
        super().run(self.__token)

    async def reload_emoji_cache(self):
        """
        Reloads emoji cache by looking up the emoji objects from the cached
        strings...
        """
        await self._loaded_emojis_raw.read_from_file()
        self._loaded_emoji_cache.clear()
        for emoji in self._loaded_emojis_raw.get():
            actual = dutils.find(
                lambda e: str(e) == emoji or e.name == emoji, self.emojis)
            if actual is None:
                self.logger.warning(f'Could not find emoji {emoji}')
            else:
                self.logger.info(f'Found emoji {emoji} as {str(actual)}')
                self._loaded_emoji_cache.append(actual)

    async def recompile_patterns(self):
        """
        Reloads and compiles the patterns.
        """
        await self._patterns_raw.read_from_file()
        self._patterns_cache.clear()
        for pattern in self._patterns_raw.get():
            regex = re.compile(pattern, flags=re.I | re.U | re.M)
            self.logger.info(f'Loaded pattern {pattern}')
            self._patterns_cache.append(regex)

    @property
    def loaded_emojis(self):
        """Gets the loaded emojis as a list."""
        return copy.copy(self._loaded_emoji_cache)

    async def set_emoji_list(self, value):
        """Sets the emoji list."""
        await self._loaded_emojis_raw.set([str(e) for e in value])
        self.logger.info('Emoji list has been changed by a commander. '
                         'Recache time!')
        asyncio.ensure_future(self.reload_emoji_cache())
        self.logger.info(f'Finished. I now have '
                         f'{len(self._loaded_emoji_cache)} emojis')

    @property
    def patterns(self):
        """Gets a list of regex patterns to react to on match."""
        return copy.copy(self._patterns_cache)

    async def set_pattern_list(self, patterns):
        """Sets the list of patterns."""
        # Get the regex patterns.
        patterns = [pattern.pattern for pattern in patterns]
        await self._patterns_raw.set(patterns)
        await self.recompile_patterns()
