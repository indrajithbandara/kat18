import random
import re

import discord
import discord.ext.commands as commands

import kat18.util as util


class Admin:
    """
    Administrative tasks.
    """
    def __init__(self):
        # Might be nicer to also have "@botuser get invite" as a command if
        # "@botuser add me" is not intuitive enough for me to remember.
        self.add_group.command(
            name='me',
            brief='Gets an invite URL.'
        )(self.add_guild)
        self.get_group.command(
            name='invite',
            brief='Gets an invite URL.'
        )(self.add_guild)

        self.remove_group.command(
            name='guild',
            aliases=['guilds', 'server', 'servers'],
            brief='Makes me leave a given server.'
        )(self.remove_guild)
        commands.command(
            name='leave',
            brief='Makes me leave a given server.'
        )(self.remove_guild)

    @staticmethod
    async def __local_check(ctx):
        return (await ctx.bot.is_owner(ctx.author)
                or ctx.author.id in ctx.bot.commanders)

    @util.group(name='get', aliases=['list'], brief='Lists various elements.')
    async def get_group(self, ctx):
        pass

    @get_group.command(
        name='commanders',
        aliases=['commander'],
        brief='Lists the current commanders for my bot.'
    )
    async def get_commanders(self, ctx):
        """Lists any commanders authorized to use me."""
        embed = discord.Embed(
            title=f'Authorized commanders for {ctx.bot.user} are',
            color=0x00FFFF,
        )

        embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        user_strings = []

        for id in ctx.bot.commanders:
            # Use the cached version or we will be dead before the
            # command finishes execution.
            user = ctx.bot.get_user(id)

            if ctx.guild is not None and user in ctx.guild.members:
                user_strings.append(f'- {user.mention} `{user.id}`')
            else:
                user_strings.append(f'- {user} `{user.id}`')

        embed.description = '\n'.join(user_strings)
        msg = await ctx.send(embed=embed)
        util.confirm_operation(ctx)
        util.make_closeable(ctx, msg)

    @get_group.command(
        name='guilds',
        aliases=['guild', 'server', 'servers'],
        brief='Lists the guilds I am part of.'
    )
    async def get_guilds(self, ctx):
        """Lists all guilds I am currently connected to."""
        embed = discord.Embed(
            title=f'{ctx.bot.user} is currently a member in',
            color=0xFFFF00
        )

        for guild in ctx.bot.guilds:
            d = [
                f'**ID**: `{guild.id}`',
                f'**Text Channels**: {len(guild.text_channels)}',
                f'**Voice Channels**: {len(guild.voice_channels)}',
                f'**Categories**: {len(guild.categories)}',
                f'**Members**: {len(guild.members)}',
                f'**MFA**: {"2FA" if guild.mfa_level else "None"}',
                f'**Verif\'n Level**: {guild.verification_level}',
                f'**Content Filter**: {guild.explicit_content_filter}',
                f'**Owner**: {guild.owner} `{guild.owner.id}`'
            ]

            if len(embed.fields) == 0:
                embed.set_thumbnail(url=guild.icon_url)

            embed.add_field(
                name=guild.name,
                value='\n'.join(d),
                inline=False
            )

        msg = await ctx.send(embed=embed)
        util.confirm_operation(ctx)
        util.make_closeable(ctx, msg)

    @commands.check(commands.guild_only())
    @get_group.command(
        name='perms',
        aliases=['perm', 'permission', 'permissions'],
        brief='Lists the permissions for this guild that I am granted.',

    )
    async def get_permissions(self, ctx):
        """Lists the current permissions the bot has in the current guild."""

        perms = ctx.guild.me.guild_permissions
        truthy_perms = [p[0] for p in perms if p[1]]
        falsey_perms = [p[0] for p in perms if not p[1]]

        truthy_perms = '\n'.join(map(str, truthy_perms))
        falsey_perms = '\n'.join(map(str, falsey_perms))

        embed = discord.Embed(
            title=f'My permissions in {ctx.guild}',
            color=0xFF00FF
        )

        embed.set_thumbnail(url=ctx.guild.icon_url)

        embed.add_field(
            name='Permissions granted',
            value=truthy_perms if truthy_perms else 'None'
        )
        embed.add_field(
            name='Permissions denied',
            value=falsey_perms if falsey_perms else 'None'
        )

        msg = await ctx.send(embed=embed)
        util.confirm_operation(ctx)
        util.make_closeable(ctx, msg)

    @get_group.command(
        name='emojis',
        aliases=['emoji', 'emote', 'emotes', 'emoticon', 'reaction' 
                 'emoticons', 'react', 'reacts', 'reactions'],
        brief='Lists the emojis that I will currently react with.'
    )
    async def get_emojis(self, ctx):
        embed = discord.Embed(
            title=f'My super dank list of emojis to shitpost with',
            color=0xFFAACC
        )

        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        emojis = ctx.bot.loaded_emojis
        embed.description = '\n'.join(
            map(lambda e: f'{str(e)} {e.name} {e.id}', emojis)
        )

        msg = await ctx.send(embed=embed)
        util.confirm_operation(ctx)
        util.make_closeable(ctx, msg)

    @get_group.command(
        name='blacklist',
        brief='Gets the blacklisted channels to not react in.'
    )
    async def get_blacklist(self, ctx):
        """
        This blacklist exists to ensure that the bot does not react in
        inappropriate situations.
        """
        blacklist = ctx.bot.dont_react_in.get()

        embed = discord.Embed(
            title='Channels I am not allowed to react in',
            description='These are the channels I am not allowed to react to '
                        'messages in...',
            color=0xB000B5
        )

        # Guild is a string. JSON standard says we can't use ints as keys.
        # Bloody stupid.
        for guild, channels in blacklist.items():
            guild_obj = discord.utils.find(
                lambda g: str(g.id) == guild,
                ctx.bot.guilds
            )

            if guild_obj is None:
                continue

            channel_objs = []
            for channel in channels:
                chan_obj = discord.utils.find(
                    lambda c: c.id == channel,
                    guild_obj.text_channels
                )

                if chan_obj is None:
                    continue

                channel_objs.append(chan_obj)

            embed.add_field(
                name=guild_obj.name,
                value='\n'.join(map(lambda c: f'#{c.name}', channel_objs)),
                inline=False
            )

        if len(embed.fields) == 0:
            embed.add_field(
                name='I am a free bot.',
                value='Nothing is blacklisted!'
            )

        msg = await ctx.send(embed=embed)
        util.confirm_operation(ctx)
        util.make_closeable(ctx, msg)

    @get_group.command(
        name='trigger',
        aliases=['triggers', 'word', 'words', 'regex', 'regexes', 'regexs',
                 'pattern', 'patterns', 'phrase', 'phrases'],
        brief='Lists all phrases/regular expressions I understand.'
    )
    async def get_phrases(self, ctx):
        # noinspection PyProtectedMember
        patterns = []

        for pattern in ctx.bot.patterns:
            # Determines if the regex was probably added as a word.
            match = re.match(r'\\b\(([^)]+)\)\\b', pattern.pattern)
            if match:
                patterns.append(match.group(1))
            else:
                patterns.append(f'`{pattern.pattern}` (regex)')

        embed = discord.Embed(
            title=f'Things I react to',
            description='\n'.join(
                patterns
            ),
            color=0xFEC
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        msg = await ctx.send(embed=embed)
        util.confirm_operation(ctx)
        util.make_closeable(ctx, msg)


    """
    'Add' commands
    """

    @util.group(name='add', brief='Adds various elements.')
    async def add_group(self, ctx):
        pass

    # Apparently making a staticmethod shits across the resolution of coro-s
    # ... thanks Guido.
    # noinspection PyMethodMayBeStatic
    async def add_guild(self, ctx, *, user: commands.MemberConverter=None):
        """
        DM's you the invite to the server. If you mention someone, then they
        get sent a URL instead of you.
        """
        if user is None:
            user = ctx.author
        await user.send(f'Add me to your server, please.\n\n{ctx.bot.invite}')
        util.confirm_operation(ctx)

    # noinspection PyUnresolvedReferences
    @commands.check(commands.guild_only())
    @add_group.command(
        name='commander',
        brief='Authorizes a user to talk on my behalf.'
    )
    async def add_commander(self, ctx, *, commander: commands.MemberConverter):
        commanders = ctx.bot.commanders.get()

        if commander == ctx.bot.user:
            raise NameError('I am not going to command _myself_...')
        elif commander.bot:
            raise NameError('I am not going to be controlled by a lowlife bot!')
        elif commander.id in commanders:
            raise NameError('That name is already in my list. Tough luck.')
        else:
            commanders.append(commander.id)
            # Commit to disk
            await ctx.bot.commanders.set(commanders)
            util.confirm_operation(ctx)

    @commands.check(commands.guild_only())
    @add_group.command(
        name='emoji',
        aliases=['emote', 'emoticon', 'reaction', 'react'],
        brief='Adds a new emoji to my reaction list.'
    )
    async def add_emoji(self, ctx, *, emote: commands.EmojiConverter):
        emotes = ctx.bot.loaded_emojis
        if emote not in emotes:
            emotes.append(emote)
            await ctx.bot.set_emoji_list(emotes)
            util.confirm_operation(ctx)
        else:
            raise ValueError(f'Emote already exists in my list. {emote}')

    @add_group.command(
        name='regex',
        aliases=['pattern'],
        brief='Adds a regular expression to Kat. Ask Espy.'
    )
    async def add_pattern(self, ctx, *, phrase: str):
        """Compiles the given regular expression."""
        regex = re.compile(phrase, flags=re.I)
        # Will assert that this compiled? Maybe?
        regex.match('')
        patterns = ctx.bot.patterns
        patterns.append(regex)
        await ctx.bot.set_pattern_list(patterns)
        util.confirm_operation(ctx)

    @add_group.command(
        name='word',
        aliases=['phrase'],
        brief='Adds a word or phrase to the list of things I can react to.',
    )
    async def add_word(self, ctx, *, phrase: str):
        """Compiles the given phrase into a regular expression."""
        # Hacky, but if I put brackets around said phrase... it should make
        # sure I detect that this is a command added word, then in the list
        # we don't have to show it in backticks. Hacky work around. Sue me, etc.
        regex = re.compile('\\b(%s)\\b' % phrase, flags=re.I | re.U | re.M)
        # Will assert that this compiled? Maybe?
        patterns = ctx.bot.patterns
        patterns.append(regex)
        await ctx.bot.set_pattern_list(patterns)
        util.confirm_operation(ctx)

    @commands.check(commands.guild_only())
    @add_group.command(
        name='blacklist',
        brief='Blacklists a given channel, or if unspecified, __this__ channel.'
    )
    async def add_blacklist(self, ctx, *,
                            channel: commands.TextChannelConverter=None):
        if channel is None:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        chan_id = channel.id

        blacklist = ctx.bot.dont_react_in.get()

        if guild_id in blacklist:
            if chan_id in blacklist[guild_id]:
                raise ValueError(f'{channel.name} is already blacklisted on '
                                 'this server.')
            else:
                blacklist[guild_id].append(chan_id)
        else:
            blacklist[guild_id] = [chan_id]

        await ctx.bot.dont_react_in.set(blacklist)
        util.confirm_operation(ctx)

    """
    'Remove' methods.
    """

    @util.group(name='remove', brief='Removes various elements.')
    async def remove_group(self, ctx):
        pass

    # noinspection PyMethodMayBeStatic
    async def remove_guild(self, ctx, *, guild):
        """
        Removes my user from a given server.
        """
        # Try to find the guild.
        guild_obj = discord.utils.find(
            lambda g: g.name.lower() == guild.lower() or g.id == guild,
            ctx.bot.guilds
        )

        if guild_obj is None:
            raise ValueError('Could not find a guild with that name or ID.')
        else:
            if ctx.guild == guild_obj:
                # We can't react after we have left.
                await ctx.message.add_reaction('\N{OK HAND SIGN}')
                await guild_obj.leave()
            else:
                await guild_obj.leave()
                util.confirm_operation(ctx)

    @remove_group.command(
        name='commander',
        aliases=['commanders'],
        brief='De-authenticates a given commander from using me.'
    )
    async def remove_commander(self, ctx, *, member: commands.MemberConverter):
        """Removes a commander from my authenticated list."""
        # Don't allow removal of the bot owner.
        if await ctx.bot.is_owner(member):
            raise PermissionError('You cannot remove the bot owner.')
        else:
            commanders = ctx.bot.commanders.get()
            commanders.remove(member.id)
            await ctx.bot.commanders.set(commanders)
            util.confirm_operation(ctx)

    @remove_group.command(
        name='regex',
        aliases=['pattern', 'word', 'phrase'],
        brief='Removes a given regex or phrase.'
    )
    async def remove_pattern(self, ctx, *, pattern):
        """
        Removes the given pattern from the list of patterns I react to.
        """
        regex = discord.utils.find(
            lambda r: r.pattern == pattern,
            ctx.bot.patterns
        )

        if regex is None:
            regex = discord.utils.find(
                lambda r: r.pattern.lower() == f'\\b({pattern.lower()})\\b',
                ctx.bot.patterns
            )

        if regex is None:
            raise ValueError('Could not find that pattern.')
        else:
            patterns = ctx.bot.patterns
            patterns.remove(regex)
            await ctx.bot.set_pattern_list(patterns)
            util.confirm_operation(ctx)

    @remove_group.command(
        name='emoji',
        aliases=['emote'],
        brief='Removes an emote from my list of reactions.'
    )
    async def remove_emoji(self, ctx, *, emoji: commands.EmojiConverter):
        """Removes the emoji from my reaction list, if it is there."""
        emojis = ctx.bot.loaded_emojis
        if emoji not in emojis:
            raise ValueError('That emoji is not registered.')
        else:
            emojis.remove(emoji)
            await ctx.bot.set_emoji_list(emojis)
            util.confirm_operation(ctx)

    @commands.check(commands.guild_only())
    @remove_group.command(
        name='blacklist',
        brief='Un-blacklists a given channel, or if unspecified, '
              '__this__ channel.'
    )
    async def remove_blacklist(self, ctx, *,
                               channel: commands.TextChannelConverter=None):
        if channel is None:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        chan_id = channel.id

        blacklist = ctx.bot.dont_react_in.get()

        if guild_id not in blacklist:
            if chan_id not in blacklist[guild_id]:
                raise ValueError(f'{channel.name} is not blacklisted on '
                                 'this server anyway.')
            else:
                blacklist[guild_id].remove(chan_id)
        else:
            blacklist.pop(guild_id)

        await ctx.bot.dont_react_in.set(blacklist)
        util.confirm_operation(ctx)

    @util.command(
        name='stop',
        aliases=['kill', 'reboot', 'restart', 'logout', 'exit', 'quit'],
        brief='Kills the bot process (Generally causes bot to restart).'
    )
    async def stop(self, ctx):
        await ctx.send(
            random.choice([
                'Yessir!',
                'Sure.',
                'Do I really have to?',
                'Goodbye ;-;',
                '*cries*...\n\n*sniffle* ...o..okay...',
                '*deletes the other bots',
                '*hisses*',
                '*nods*',
                'kk',
                'k',
                'Sure thing sauce boss.',
                'Gimme a sec then!',
                'Okydokes',
                'Ja.',
                'PlEaSe ShUtDoWn FoR Me BoT!',
                'Meh',
                'You are no fun...',
                'Soon. Soon you will regret the day you messed with --'
                '*powers down*'
            ])
        )
        await ctx.bot.logout()


def setup(bot):
    bot.add_cog(Admin())
