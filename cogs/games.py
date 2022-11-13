import discord
import random
import logging
from discord import ApplicationContext
from discord.ext import commands
from discord.commands import slash_command, SlashCommandGroup, Option
from utils.Logger import Logger

logger = logging.getLogger('livebot')

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_users = ()

    guild_ids = []

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Games Loaded')

    @slash_command(description="Among us Rules", guild_ids=guild_ids)
    async def amg(self, ctx: ApplicationContext):
        embed = discord.Embed(
        title = 'Among Us Rules',
        description = 'These are the rules that we play by in this discord',
        colour = discord.Colour.orange()
        )

        embed.add_field(name='1.', value='During play **ALL** Mics are to be muted. Only unmute during **Meetings**.', inline=False)
        embed.add_field(name='2.', value='If killed, you can **NOT** speak until the game has been completed, you can use text chat however.', inline=False)
        embed.add_field(name='3.', value='Have fun, Dont be an idiot.', inline=False)
        await ctx.respond(embed=embed)

    @slash_command(description="Among Us settings", guild_ids=guild_ids)
    async def aset(self, ctx: ApplicationContext):
        embed = discord.Embed(
        title='Optimal Among Us Settings',
        description = 'Use these settings for the most fun',
        colour=discord.Colour.orange()
        )

        embed.add_field(name='Imposters', value='2 (lobby of 10), 1 (lobby < 10)', inline=False)
        embed.add_field(name='Confirm Ejects', value='Confirm Ejects = Off', inline=False)
        embed.add_field(name='Emergency Meetings', value='1', inline=False)
        embed.add_field(name='Emergency Cooldown', value='15s', inline=False)
        embed.add_field(name='Discussion Time', value='15s', inline=False)
        embed.add_field(name='Voting Time', value='120s', inline=False)
        embed.add_field(name='Player Speed', value='1x', inline=False)
        embed.add_field(name='Crewmate Vision', value='0.75x', inline=False)
        embed.add_field(name='Imposter Vision', value='1.5x', inline=False)
        embed.add_field(name='Kill Cooldown', value='22.5s', inline=False)
        embed.add_field(name='Kill Distance', value='Short', inline=False)
        embed.add_field(name='Visual Tasks', value='Off', inline=False)
        embed.add_field(name='Common Tasks', value='2', inline=False)
        embed.add_field(name='Long Tasks', value='2', inline=False)
        embed.add_field(name='Short Tasks', value='5', inline=False)

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Games(bot))
