import random
import discord
import pymysql
import math
import logging
from discord import ApplicationContext
from discord.commands import slash_command, Option
from discord.ext import commands
from utils.Logger import Logger

logger = logging.getLogger('livebot')
guild_ids = []

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_users = ()
        self.connection = pymysql.connect(
            host='raspberrypi',
            user='pi',
            password='',
            database='Guilds',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Moderation Loaded")

    #adds a word to the ban list
    @slash_command(description="Used to add a banned word to the server", guild_ids=guild_ids)
    @commands.has_role("Great Apes")
    async def bw(self, ctx, word: Option(str, "The word to be banned", default=None)):
        connection = self.connection
        
        if word == None:
            return await ctx.respond("You must provide a word that you would like to ban.")
        
        with connection.cursor() as cursor:
            sql = "INSERT INTO Banned_Words (guild_id, word) VALUES ({},'{}')".format(ctx.guild.id, word)
            print(sql)
            connection.ping()
            cursor.execute(sql)
            connection.commit()

            await ctx.respond(f"`{word}` has been added to the list of banned words.")

    #shows the banned words list
    @slash_command(description="Shows the list of banned words for the server", guild_ids=guild_ids)
    async def wl(self, ctx, page: Option(int, "Page Number", default=1)):
        connection = self.connection
        with connection.cursor() as cursor:
            sql = "SELECT word WHERE guild_id = {}".format(ctx.guild.id)
            connection.ping()
            cursor.execute(sql)
            results = cursor.fetchall()

            embed = discord.Embed(
                    title = 'Banned Words',
                    description = 'A list of words that have been banned.',
                    colour = discord.Colour.orange()
                )

            wordList = []
            for word in results:
                wordList.append(word['word'])
            
            items_per_page = 20
            pages = math.ceil(len(wordList) / items_per_page)
            start = (page - 1) * items_per_page
            end = start + items_per_page
            role_list = ''

            for i, rol in enumerate(wordList[start:end], start=start):
                role_list += f'`{i + 1}.` {rol}\n'
            randColour = random.randint(0, 0xffffff)
            embed = discord.Embed(
                title=f'Words Banned: {len(wordList)}',
                description=f'{role_list}\n',
                colour=randColour
            )
            embed.set_footer(text=f'Viewing Page: {page}/{pages}')
        await ctx.respond(embed=embed)

    #clears banned word list
    @slash_command(description="Clears banned words list", guild_ids=guild_ids)
    @commands.has_role("Great Apes")
    async def cwl(self, ctx: ApplicationContext):
        connection = self.connection
        with connection.cursor() as cursor:
            sql = "DELETE * FROM Banned_Words WHERE guild_id = %s"
            connection.ping()
            cursor.execute(sql, ctx.guild.id)
            connection.commit()
        await ctx.respond("The Banned Words have been cleared.")

    #clears warnings
    @slash_command(description="Clears all the warnings for users", guild_ids=guild_ids)
    @commands.has_role("Great Apes")
    async def cwarn(self, ctx: ApplicationContext):
        connection = self.connection
        with connection.cursor() as cursor:
            sql = "UPDATE users SET warned = 0 WHERE guild_id = %s"
            connection.ping()
            cursor.execute(sql, ctx.guild.id)
            connection.commit()
        await ctx.respond("You have set all warnings to 0.")

    @slash_command(description="Mutes everyone in the channel", guild_ids=guild_ids)
    @commands.has_any_role("Great Apes")
    async def mute(self, ctx: ApplicationContext):
        vChannel = ctx.author.voice.channel
        for member in vChannel.members:
            await member.edit(mute=True)

    @slash_command(description="Unmutes all users in the voice channel", guild_ids=guild_ids)
    @commands.has_any_role("Great Apes")
    async def unmute(self, ctx: ApplicationContext):
        vChannel = ctx.author.voice.channel
        for member in vChannel.members:
            await member.edit(mute=False)

    @slash_command(description="Gets information about a user", guild_ids=guild_ids)
    async def userinfo(self, ctx: ApplicationContext, user: Option(discord.Member, "User to gain info about")):
        e = discord.Embed(
            title= f"{ctx.author.display_name}'s Information",
            description= '',
            colour = discord.Colour.orange()
        )

        joined_at = user.joined_at.strftime("%b %d, %Y")

        e.add_field(name='Joined the Server: ', value=f'`{joined_at}`', inline=True)
        e.add_field(name='User Created On: ', value=f'`{user.created_at.strftime("%b %d, %Y")}`', inline=True)
        rolelist = [r.name for r in user.roles if r != ctx.guild.default_role]
        rolelist.reverse()
        roles = '\n'.join(rolelist)
        e.add_field(name='Roles: ', value=f'`{roles}`', inline=False)
        e.set_footer(text=f'{user}', icon_url=f'{user.display_avatar}')

        async with ctx.typing():
            await ctx.respond(embed=e)

    @slash_command(description="Gets information about the server", guild_ids=guild_ids)
    async def serverinfo(self, ctx: ApplicationContext):
        e = discord.Embed(
            title=ctx.guild.name,
            colour = discord.Colour.orange()
        )

        e.add_field(name='Server Owner: ', value=ctx.guild.owner.name, inline=False)
        e.add_field(name='Server Created: ', value=ctx.guild.created_at.strftime("%b %d, %Y"), inline=False)
        e.add_field(name='Server Location: ', value=ctx.guild.region, inline=False)
        e.add_field(name='Active Boosts: ', value=ctx.guild.premium_subscription_count)
        e.add_field(name='Total Members: ', value=ctx.guild.member_count, inline=False)
        e.add_field(name='Server ID: ', value=ctx.guild.id, inline=False)
        
        
        e.set_thumbnail(url=ctx.guild.icon_url)
        async with ctx.typing():
            await ctx.respond(embed=e)

    @slash_command(description="Guild ID", guild_ids=guild_ids)
    @commands.has_role("Great Apes")
    async def gid(self, ctx: ApplicationContext):
        await ctx.respond('Printed')
        print(ctx.guild.id)
        
def setup(bot):
    bot.add_cog(Mod(bot))
