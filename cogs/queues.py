import discord
import pymysql
import lavalink
import re
import math
import random
import os
import logging
from discord import ApplicationContext
from discord.ext import commands
from discord.commands import slash_command, Option
from discord.colour import Colour
from utils.Logger import Logger
from utils.Database import Database

url_rx = re.compile(r'https?://(?:www\.)?.+')
time_rx = re.compile('[0-9]+')
logger = logging.getLogger('livebot')
guild_ids = []

class Queues(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.allowed_users = ()
        self.connection = pymysql.connect(
            host='raspberrypi',
            user='pi',
            password='',
            database='Guilds',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def checkForQueue(self):
        connection = self.connection
        with connection.cursor() as cursor:
            sql="SHOW TABLES"
            connection.ping()
            results = cursor.execute(sql)

            if results == None:
                return

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Queues Loaded")

    @slash_command(description="Makes a queue from the current song queue", guild_ids=guild_ids)
    @commands.has_role('Great Apes')
    async def addqueue(self, ctx: ApplicationContext, queue: Option(str, "The queue name", default=None)):
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        connection = self.connection
        
        if queue is None:
            pass
        else:
            queue = queue.lower()

        with connection.cursor() as cursor:
            sql = "INSERT INTO queues (queue, guild_id, bot_id) VALUES ('{}',{},{})".format(queue, ctx.guild.id, self.client.user.id)
            connection.ping()
            cursor.execute(sql)
            connection.commit()
            print(f"Added {queue} to queue names table")

        with connection.cursor() as cursor:
            tableName = f"{queue}-{self.client.user.id}"
            sql = "CREATE TABLE IF NOT EXISTS `{}` (id INT AUTO_INCREMENT PRIMARY KEY, song VARCHAR(255))".format(tableName)
            connection.ping()
            cursor.execute(sql)
            connection.commit()
            
        if player.queue:
            print("Adding songs to the table.")
            with connection.cursor() as cursor:
                for i, track in enumerate(player.queue):
                    tableName = f"{queue}-{self.client.user.id}"
                    trackTitle = track.title
                    trackTitle = trackTitle.replace("'", "")
                    trackTitle = trackTitle.replace('"', "")
                    sql = "INSERT INTO `{}` (`id`, `song`) VALUES (0, '{}')".format(tableName, trackTitle)
                    connection.ping()
                    cursor.execute(sql)
                    connection.commit()
                    print(f"Added `{trackTitle}` into the table: `{queue}`")
            await ctx.respond(f"`{queue}` has been created.")

    @slash_command(description="Deletes an existing queue", guild_ids=guild_ids)
    async def deletequeue(self, ctx: ApplicationContext, queue: Option(str, "The queue to delete", default=None)):
        connection = self.connection
        currentUser = ctx.author
        role = discord.utils.get(ctx.guild.roles, name='DJ')
        tableName = f"{queue}-{self.client.user.id}"
        if role in currentUser.roles:
            if queue == 'queues':
                return await ctx.respond("You can not delete that. Use the queues command to see what queues can be deleted.")

            if self.checkForQueue():
                with connection.cursor() as cursor:
                    sql = "DELETE FROM queues WHERE queue = '%s' AND guild_id = %s AND bot_id = %s LIMIT 1"
                    connection.ping()
                    cursor.execute(sql, (queue, ctx.guild.id, self.client.user.id))
                    connection.commit()

                with connection.cursor() as cursor:
                    sql = "DROP TABLE IF EXISTS `{}`".format(tableName)
                    connection.ping()
                    cursor.execute(sql)
                    connection.commit()

                    await ctx.respond(f"Deleted queue save: `{queue}`")

        else:
            await ctx.respond('You dont have permission to use that command. Message an Admin for permission.')

    @slash_command(description="lists the saved queues", guild_ids=guild_ids)
    async def queues(self, ctx: ApplicationContext, page: Option(int, "Page Number", default=1)):
        result = Database.get("queue", "queues", ctx.guild.id, self.client.user.id, "queues")

        embed = discord.Embed(
            title = 'Saved Queues',
            description = 'A list of Queues that have been saved.',
            colour = discord.Colour.orange()
        )

        queueList = []

        for title in result:
            queueList.append(title['queue'])
        
        items_per_page = 20
        pages = math.ceil(len(queueList) / items_per_page)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        role_list = ''

        for i, rol in enumerate(queueList[start:end], start=start):
            role_list += f'`{i + 1}.` {rol}\n'
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(
            title=f'Queues in the List: {len(queueList)}',
            description=f'{role_list}\n',
            colour=randColour
        )
        embed.set_footer(text=f'Viewing Page: {page}/{pages}')
        await ctx.respond(embed=embed)

    @slash_command(description="adds songs to a saved queue", guild_ids=guild_ids)
    async def editqueue(self, ctx: ApplicationContext, queue: Option(str, "The queue to edit"), *, list: Option(str, "The list of songs to add")):
        if list is None:
            return

        tableName = f"{queue}-{self.client.user.id}"
        songs = list.split(', ')
        i = 0
        while i < len(songs):
            Database.update(tableName, songs[i], "queues")
            i += 1
        await ctx.respond(f"{queue} was updated with all of your songs.")

def setup(client):
    client.add_cog(Queues(client))

