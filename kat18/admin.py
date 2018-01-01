import discord
import discord.ext.commands as commands

import kat18.util as util


class Admin:
    """
    Administrative tasks.
    """
    @util.group(name='list', brief='Lists various elements.')
    async def list_group(self, ctx):
        pass

    @list_group.command(
        name='commanders',
        aliases=['commander'],
        brief='Lists the current commanders for my bot.'
    )
    async def list_commanders(self, ctx):
        """Lists any commanders authorized to use me."""
        embed = discord.Embed(
            title=f'Authorized commanders for {ctx.bot.user} are',
            color=0x00FFFF,
        )

        embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        user_strings = []

        for id in ctx.bot.commanders:
            user = await ctx.bot.get_user_info(id)

            if ctx.guild is not None and user in ctx.guild.members:
                user_strings.append(f'- {user.mention} `{user.id}`')
            else:
                user_strings.append(f'- {user} `{user.id}`')

        embed.description = '\n'.join(user_strings)
        await ctx.send(embed=embed)

    @list_group.command(
        name='guilds',
        aliases=['guild', 'server', 'servers'],
        brief='Lists the guilds I am part of.'
    )
    async def list_guilds(self, ctx):
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

        await ctx.send(embed=embed)

    @commands.check(commands.guild_only())
    @list_group.command(
        name='perms',
        aliases=['perm', 'permission', 'permissions'],
        brief='Lists the permissions for this guild that I am granted.'
    )
    async def list_permissions(self, ctx):
        """Lists the current permissions the bot has in the current guild."""

        perms = ctx.guild.me.guild_permissions
        truthy_perms = [p[0] for p in perms if p[1]]
        falsey_perms = [p[0] for p in perms if not p[1]]

        truthy_perms = '\n'.join(map(str, truthy_perms))
        falsey_perms = '\n'.join(map(str, falsey_perms))

        embed = discord.Embed(
            title=f'Permissions in {ctx.guild} for {ctx.bot.name}',
            color=0xFF00FF
        )

        embed.set_thumbnail(url=ctx.guild.icon_url)

        embed.add_field(name='Permissions granted', value=truthy_perms)
        embed.add_field(name='Permissions denied', value=falsey_perms)

        await ctx.send(embed=embed)

    @list_group.command(
        name='emojis',
        aliases=['emoji', 'emote', 'emotes', 'emoticon', 'reaction' 
                 'emoticons', 'react', 'reacts', 'reactions'],
        brief='Lists the emojis that I will currently react with.'
    )
    async def list_emojis(self, ctx):
        pass

    @util.group(name='add', brief='Adds various elements.')
    async def add_group(self, ctx):
        pass

    @util.group(name='remove', brief='Removes various elements.')
    async def remove_group(self, ctx):
        pass

    @util.command(
        name='stop',
        aliases=['kill', 'reboot', 'restart', 'logout', 'exit', 'quit'],
        brief='Kills the bot process (Generally causes bot to restart).'
    )
    async def stop(self, ctx):
        await ctx.message.add_reaction('\N{OK HAND SIGN}')
        await ctx.bot.logout()


def setup(bot):
    bot.add_cog(Admin())
