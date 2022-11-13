import discord
import os
import re
import random
import math
import pymysql
import logging
import colorlog

from itertools import count
from datetime import datetime
from discord import embeds, DiscordException, ApplicationContext
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.bot import when_mentioned_or
from pymysql import NULL, cursors
from asyncio import sleep
from utils.Database import Database
from utils.Logger import Logger

intents = discord.Intents.all()
intents.presences = False
client = commands.AutoShardedBot(
    intents = intents,
    command_prefix= '-',
    case_insensitive=True
)
prefix = client.command_prefix
client.remove_command('help')

randColour = random.randint(0, 0xffffff)
url_regex = r"(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'\"\.,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"
gifLink = r"https://tenor\.com/.*"
gifLinkTwo = r"https://c\.tenor\.com/.*"
mediaLink = r"https?://media.discordapp.net/.*"

allowed_users = ()
cmd_allowed = ()
no_links = ()
test_cogs = 'D:\\CurrentBots\\test\\cogs'
prod_cogs = '/home/pi/bot/cogs'
test_logs = 'D:\\CurrentBots\\test\\logs\\botlogs.log'
prod_logs = "/home/pi/bot/logs/botlogs.log"
test_token = ''
prod_token = ''
roleList = []
roleListDisplay = []


logLocation = test_logs
logger = Logger.createLogs(logLocation)

connection = pymysql.connect(
        host='raspberrypi',
        user='pi',
        password='',
        database='Guilds',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_prefix(client, message):
    results = Database.get_prefix(message.guild.id, client.user.id)

    if results == None:
        logger.error("Results returned none, there is not prefix")
        return
    else:
        prefix = results['prefix'][0]

    return when_mentioned_or(prefix)(client, message)
    
@client.event
async def on_ready():
    logger.info("Livebot Ready")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Developed By Hectic'))
    
    for guild in client.guilds:
        with connection:
            with connection.cursor() as cursor:
                sql = "SELECT prefix FROM guild_info WHERE (guild_id =%s AND bot_id =%s)"
                connection.ping()
                cursor.execute(sql, (guild.id, client.user.id))
                result = cursor.fetchone()
        
        if result == None:
            with connection.cursor() as cursor:
                sql = "INSERT INTO guild_info (guild_id, prefix, bot_id) VALUES (%s,%s,%s)"
                connection.ping()
                cursor.execute(sql, (guild.id, "-", client.user.id))
                connection.commit()

            with connection.cursor() as cursor:
                sql = "SELECT prefix FROM guild_info WHERE (guild_id =%s AND bot_id =%s)"
                connection.ping()
                cursor.execute(sql, (guild.id, client.user.id))
                result = cursor.fetchone()
        
    client.command_prefix = get_prefix

############################################################################ \\COMMANDS// ####################################################################################################

#loads specified cog
@client.command()
@commands.is_owner()
async def load(message, extention):
    owner_id = client.get_user()
    if message.author.id == '':
        client.load_extension(f'cogs.{extention}')
        await owner_id.send(f'{extention} was loaded.')
    else:
        logger.error("Someone tried to use the load command.")
        await message.channel.send(f'{message.author.mention} You can not use that command. It is only used by Hectic')

#unloads specified cog
@client.command()
@commands.is_owner()
async def unload(message, extention):
    owner_id = client.get_user()
    if message.author.id == '':
        client.unload_extension(f'cogs.{extention}')
        await owner_id.send(f'{extention} was unloaded.')
    else:
        logger.error("Someone tried to use the unload command.")
        await message.channel.send(f'{message.author.mention} You can not use that command. It is only used by Hectic')

#reloads specified cog
@client.command()
@commands.is_owner()
async def reload(message, extention):
    owner_id = client.get_user()
    if message.author.id == '':
        client.unload_extension(f'cogs.{extention}')
        client.load_extension(f'cogs.{extention}')
        print(f'{extention} was reloaded.')
        await owner_id.send(f'{extention} was reloaded.')
    else:
        logger.error("Someone tried to use the reload command.")
        await message.channel.send(f'{message.author.mention} You can not use that command. It is only used by Hectic')

@client.command()
@commands.has_role("Great Apes")
async def prefix(ctx, pre: str = NULL):
    if len(pre) > 1 and not NULL:
        await ctx.send('Prefix can only be a single character.')
    elif pre == NULL:
        logger.debug('Getting Prefix')
        pref = Database.get_prefix(ctx.guild.id, client.user.id)
        logger.debug(f'prefix is: `{pref["prefix"][0]}`')
        if pref == None:
            logger.info("There was no prefix when requested. Creating it.")
            Database.createPrefix(ctx.guild.id, client.user.id)
            await ctx.send("The current prefix is: `!`")
        else:
            await ctx.send(f"The current prefix is: `{pref['prefix']}`")

    else:
        Database.updatePrefix(pre, ctx.guild.id, client.user.id)
        await ctx.send(f"You have updated the prefix to: `{pre}`")

#sends feature requests to Hectic
@client.command()
async def request(ctx, *requestMessage: str):
    requestMessage = ' '.join(requestMessage)
    notif = discord.Embed(title='Command Request Recieved.', description='Your request is sent to Hectic to be put into the bot.', color=0x960505)
    notif.add_field(name='Request Recieved', value=f'{requestMessage}')
    await ctx.send(embed=notif)

    req = discord.Embed(titel='Command Request', color=0x960505)
    req.add_field(name=f'Requested by: {ctx.author}', value=f'{requestMessage}')

    owner_id = client.get_user()
    await owner_id.send(embed=req)

#bans a user
@client.command()
@commands.has_role("Great Apes")
async def ban(ctx, member : discord.Member, *, reason=None):
    if ctx.author.id in allowed_users:
        await member.ban(reason=reason)
    else:
        await ctx.send("You dont have permission to use that command.")

#Clears messages
@client.command()
@commands.has_guild_permissions(manage_messages = True)
async def clear(ctx, amount=2):
    if ctx.author.id in allowed_users:
        await ctx.channel.purge(limit=amount)
    else:
        await ctx.send("You dont have permission to use that command.")

#kicked user from discord server
@client.command()
@commands.has_role("Great Apes")
async def kick(ctx, member : discord.Member, *, reason=None):
    if ctx.author.id in allowed_users:
        await member.kick(reason=reason)
    else:
        await ctx.send("You dont have permission to use that command.")

#shows a user's ping to the bot
@client.command()
async def ping(ctx):
    await ctx.send(f'Your Ping to the bot is: {round(client.latency * 1000)}ms')

#unbans a banned user
@client.command()
@commands.has_role("Great Apes")
async def unban(ctx, *, member):
    if ctx.author.id in allowed_users:
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.name}#{user.discriminator}')
                return
    else:
        await ctx.send("You dont have permission to use that command.")

#gives a user the muted role
@client.command(aliases=['tm'])
@commands.has_role("Great Apes")
async def tmute(ctx, member:discord.Member = None):
    mRole = discord.utils.get(member.guild.roles, name='muted')
    if ctx.author.id in allowed_users:
        if member is None:
            await ctx.send("Please enter a valid user.")
            return

        await member.add_roles(mRole)
        await ctx.send(f'{str(member)} has been muted.')
    else:
        await ctx.send("You dont have permission to use that command.")

#removes the muted role from a user
@client.command(aliases=['tu'])
@commands.has_role("Great Apes")
async def tunmute(ctx, member : discord.Member = None):
    mRole = discord.utils.get(member.guild.roles, name='muted')
    if ctx.author.id in allowed_users:
        if member is None:
            await ctx.send("Please enter a valid user.")
            return
        await member.remove_roles(mRole)
        await ctx.send(f'{str(member)} Has been unmuted.')
    else:
        await ctx.send("You dont have permission to use that command.")

################################################################## EVENTS ##############################################################

@client.event
async def on_message(message: discord.Message):   
    if not message.guild:
        user = await client.fetch_user(message.author.id)
        await user.send('I can not run commands from DMs, some may think i am the bot. But it is you who is the bot.')
        return logger.warning("Someone DM'd the bot.")
        
    #Checks if a link was posted in a non links channel
    if re.search(url_regex, message.content) and message.channel.id in no_links:
        if re.search(gifLink, message.content) or re.search(gifLinkTwo, message.content) or re.search(mediaLink, message.content):
            return await client.process_commands(message)
        else:
            dest = client.get_channel()
            await dest.send(f'{message.author.mention} Posted this link in another channel. I moved it here. \n \n {message.content}')
            await message.delete()
    else:
    #Checks for use of a banned word
        with connection.cursor() as cursor:
            sql = "SELECT word FROM Banned_Words WHERE guild_id =%s"
            connection.ping()
            cursor.execute(sql, message.guild.id)
            words = cursor.fetchall()

            msg = message.content.split(" ")

            for word in words:
                if word['word'] in msg:
                    await message.delete()
                    await message.channel.send("That is a banned word. use `wl` to see a list of banned words.")
        
        return await client.process_commands(message)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('That command does not exist. Use `-help` to see a list of commands.')
        logger.warning("Someone tried using a command that does not exist.")
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('You are missing a part of the command. Use `-help` to see the proper use of the command.')
        logger.warning("Someone tried using a command without a required argument.")
    
    elif isinstance(error, commands.BadArgument):
        await ctx.send('That argument is incorrect. Use `-help` to see the proper use of the command.')
        logger.warning("Someone tried to use an incorrect argument in a command.")

    elif isinstance(error, commands.DisabledCommand):
        await ctx.send('That command is disabled. Use `-help` to get a list of commands.')
        logger.warning('Someone tried to use a disabled command.')

    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send('I dont have permission to do that, check with Zane to make sure I get the correct permissions.')
        logger.warning('The bot was missing permissions to run the command.')

    elif isinstance(error, commands.TooManyArguments):
        await ctx.send('You added too many arguments. Use `-help` to see the proper use of the command.')
        logger.warning('Someone added too many arguments when using a command.')            

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send('That command is on cooldown. Please wait to use it again.')
        logger.warning('Someone used a command while it was on cooldown.')

    elif isinstance(error, commands.MissingRole):
        await ctx.send(f'You need the `{error.missing_role}` role to use that command, message an admin to get this fixed.')
        logger.warning(f'Someone was missing the {error.missing_role} role for a command.')

    else:
        logger.warning(error)

@client.event
async def on_application_command_error(ctx: ApplicationContext, error: DiscordException):
    logger.warning(f'An application command caused an error: {error}')
    await ctx.respond(f'An error occured')

@client.event
async def on_member_remove(member):
    goodbye = discord.utils.get(client.get_all_channels(), name='general')
    await goodbye.send(f'Goodbye {member.mention}')
    
@client.event
async def on_member_join(member):
    welcome = discord.utils.get(client.get_all_channels(), name='general')
    await welcome.send(f'Welcome to the server {member.name}')
    

for filename in os.listdir(test_cogs):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(test_token)
