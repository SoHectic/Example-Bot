import discord
import random
import os
import praw
import aiohttp
import logging
from discord import ApplicationContext
from discord.commands import slash_command, Option
from discord.ext import commands, tasks
from discord.utils import get
from utils.Logger import Logger

logger = logging.getLogger('livebot')
guild_ids = []

class memes(commands.Cog):
    """Meme Commands"""
    def __init__(self, bot):
        self.bot = bot
        self.allowed_users = ()
        
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Memes Loaded")
    
    @slash_command(description="A description of baker", guild_ids=guild_ids)
    async def baker(self, ctx: ApplicationContext):
        """'baker'"""
        await ctx.respond('Baker is a loud rage monster that watches videos and eats Doritos all with an open mic.')

    @slash_command(description="A description of Danny", guild_ids=guild_ids)
    async def danny(self, ctx: ApplicationContext):
        """'danny'"""
        await ctx.respond('Danny is deaf and lives in a cave.')

    @slash_command(description="shows a random Tommy quote", guild_ids=guild_ids)
    async def tommy(self, ctx: ApplicationContext):
        channel = self.client.get_channel()
        messages = await channel.history().flatten()
        msgChoice = random.randint(0, len(messages))
        quote = await channel.fetch_message(messages[msgChoice].id)
        
        async with ctx.typing():
            await ctx.respond(quote.content)

    @slash_command(description="Chooses a random tarkov map and person to have a veto", guild_ids=guild_ids)
    async def map(self, ctx: ApplicationContext):
        """'-map'"""
        maps = ["Customs",
                "Reserv",
                "Interchange",
                "Shoreline",
                "Factory",
                "Woods",
                "Labs",
                "Lighthouse"
        ]
        await ctx.respond(f'{random.choice(maps)}')
        vChannel = ctx.message.author.voice.channel
        members = vChannel.members
        connected= []

        for member in members:
            connected.append(member.name)
        await ctx.respond(f'{random.choice(connected)} was chosen for Veto.')

    @slash_command(description="Displays a random meme from r/memes")
    async def meme(self, ctx: ApplicationContext):
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(
            title = '',
            description = '',
            colour = randColour
        )

        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://www.reddit.com/r/memes/new.json?sort=hot') as r:
                res = await r.json()
                randNum = random.randint(0, 25)
                embed.set_image(url=res['data']['children'][randNum]['data']['url'])
                embed.title = res['data']['children'][randNum]['data']['title']
                await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(memes(bot))