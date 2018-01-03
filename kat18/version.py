import discord
import kat18.util


@kat18.util.command()
async def about(ctx):
    embed = discord.Embed(
        title=f'{kat18.__title__} {kat18.__version__}',
        description='\n\n'.join([
            f'Created by: {kat18.__author__}',
            f'Repository: {kat18.__repository__}',
            f'Licenced under: {kat18.__license__}'
        ]),
        color=0x391841,
        url=kat18.__repository__
    )

    embed.set_thumbnail(url=ctx.bot.user.avatar_url)

    embed.set_footer(text='No purrloins were hurt in the making of this bot.')

    await ctx.send(embed=embed)


def setup(bot):
    bot.add_command(about)