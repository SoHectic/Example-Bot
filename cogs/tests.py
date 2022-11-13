import discord
import logging
from discord.ext import commands
from discord.commands import slash_command, Option
from utils.Logger import Logger
from utils.Database import Database

logger = logging.getLogger('livebot')
guild_ids = []

class Tests(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Tests Loaded")

    @slash_command(description="Used to test the prefix fetch", guild_ids=guild_ids)
    @commands.is_owner()
    async def testprefix(self, ctx):
        results = Database.get_prefix(ctx.guild.id, self.client.user.id)
        print(results['prefix'][0])
        await ctx.respond(f"The prefix from the test returned: {results['prefix'][0]}")

def setup(client):
    client.add_cog(Tests(client))
