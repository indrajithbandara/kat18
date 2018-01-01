"""
Class that implements the Bot class.
"""
import json
import discord.ext.commands as commands
import kat18.util as util


extensions = {
    'kat18.talk',
    'kat18.presence',
    'kat18.admin'
}


class KatBot(commands.Bot, util.Loggable):
    """Kat bot client."""

    def __init__(self, config_file):
        """
        Init the client.
        :param config_file: path of the config JSON file to open.
        """
        with open(config_file) as fp:
            config: dict = json.load(fp)

        self.config_file = config_file
        self.config = config

        super().__init__(command_prefix=commands.when_mentioned,
                         owner_id=config['owner_id'])

        self.logger.info(f'Add me to a guild at: {self.invite}')

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

    @property
    def commanders(self):
        """Gets the commanders list."""
        commanders = self.config.get('commanders', None)
        if not commanders:
            commanders = {self.owner_id}
            self.commanders = commanders
        else:
            return set(commanders)
        return commanders

    @commanders.setter
    def commanders(self, new_set):
        """Sets the commanders list."""
        assert isinstance(new_set, set)
        for element in new_set:
            assert isinstance(element, int)

        # Ensure the owner is always a commander.
        new_set.add(self.owner_id)

        self.config['commanders'] = list(new_set)

        with open(self.config_file, 'w') as fp:
            # Write the file again.
            self.logger.info(f'Successfully wrote out {self.config_file}')
            json.dump(self.config, fp=fp, indent=' ' * 4)

    def run(self):
        """Runs the bot."""
        super().run(self.__token)
