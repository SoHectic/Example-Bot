import discord
import pymysql
import logging
from asyncio import sleep
from discord.ext import commands
from discord.commands import slash_command, Option
from discord.partial_emoji import PartialEmoji
from discord.colour import Colour
from discord.utils import get
from utils.Logger import Logger
from utils.Database import Database

#704447683636494427 - DJ
#816814760561213460 - Tarkov
#816814779145781298 - Amongus
#816814806803415090 - Ark
#835903047380631623 - Minecraft
#907346922589802516 - Battlefield
role_ids = []
guild_ids = []
logger = logging.getLogger('livebot')

allowed_users = ()
connection = pymysql.connect(
            host='raspberrypi',
            user='pi',
            password='',
            database='Guilds',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

def getRoles(guild_id):
    tableName = f"roles-{guild_id}"
    with connection.cursor() as cursor:
        sql = "SELECT role_id FROM `{}` WHERE guild_id =%s".format(tableName)
        connection.ping()
        cursor.execute(sql, guild_id)
        results = cursor.fetchall()
        return results



class Roles(discord.ui.Button):
    def __init__(self, role: discord.Role):
        """
            A button for one role.
        """
        super().__init__(label=role.name, style = discord.enums.ButtonStyle.primary, custom_id=str(role.id))

    async def callback(self, interaction: discord.Interaction):
        """
            This function is called any time a user clicks on a button
            Params:
                interaction : discord.interaction
                the interaction object that was created when the user clicks the button
        """

        user = interaction.user
        role = interaction.guild.get_role(int(self.custom_id))

        if role is None:
            return

        if role not in user.roles:
            await user.add_roles(role)
            await interaction.response.send_message(f"You have been given the role: `{role}`")
            
        else:
            await user.remove_roles(role)
            await interaction.response.send_message(f'You have been removed from the role: {role}')
            

class ButtonRoles(commands.Cog):
    """
        A Cog with slash commands for posting the message with buttons to init the view when the bot is restarted
    """

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Roles Loaded")
        """This function is called every time the bot restarts.
        If a view was already created before (with the same custom IDs for buttons)
        it will be loaded and the bot will start watching for button clicks again.
        """

        # we recreate the view as we did in the /post command
        view = discord.ui.View(timeout=None)
        # make sure to set the guild ID here to whatever server you want the buttons in
        guild = self.client.get_guild()
        for role_id in role_ids:
            role = guild.get_role(role_id)
            view.add_item(Roles(role))

        # add the view to the bot so it will watch for button interactions
        self.client.add_view(view)

    @commands.slash_command(description = "Post the button role message", guild_ids=guild_ids)
    @commands.has_any_role("Great Apes")
    async def roles(self, ctx: commands.Context):
        """Slash command to post a new view with a button for each role"""
        tableName = f"roles-{ctx.guild.id}"
        results = Database.getRoles(tableName, ctx.guild.id)
        for role in results:
            role_ids.append(role['role_id'])

        # timeout is None because we want this view to be persistent
        view = discord.ui.View(timeout=None)

        # loop through the list of roles and add a new button to the view for each role
        for role_id in role_ids:
            # get the role the guild by ID
            role = ctx.guild.get_role(role_id)
            view.add_item(Roles(role))

        await ctx.respond("Click a button to assign yourself a role", view=view)

    @commands.slash_command(description = "Used to add a role to the joinable roles", guild_ids=guild_ids)
    @commands.has_any_role("Great Apes")
    async def addrole(self, ctx, role):
        tableName = f"roles-{ctx.guild.id}"
        roleN = get(ctx.guild.roles, name=role)
        
        if roleN == None:
            await ctx.respond("That is not a role, check the role list to see what roles can be added.")
            return

        roleID = roleN.id
        for roleName in ctx.guild.roles:
            if str(roleName) == role:
                with connection.cursor() as cursor:
                    sql = "REPLACE INTO `{}` (guild_id, role_id, role) VALUES (%s, %s, %s)".format(tableName)
                    connection.ping()
                    cursor.execute(sql, (ctx.guild.id, roleID, role))
                    connection.commit()

                msg = await ctx.respond(f"Added the role: {role} to the joinable roles list.")

    @commands.slash_command(description="Used to create a roles table.", guild_ids=guild_ids)
    @commands.is_owner()
    async def addtable(self, ctx):
        tableName = f"roles-{ctx.guild.id}"
        with connection.cursor() as cursor:
            sql = "CREATE TABLE IF NOT EXISTS `{}` (guild_id BIGINT(20), role_id BIGINT(20), role VARCHAR(255))".format(tableName)
            connection.ping()
            cursor.execute(sql)
            connection.commit()

            await ctx.respond("Created Role Table")

    @slash_command(description="Used to set the permission roles", guild_ids=guild_ids)
    @commands.has_guild_permissions(administrator=True)
    async def permrole(self, ctx, rolename: Option(str, "The name of the role for permissions")):
        await ctx.defer()
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        if role is None:
            return await ctx.respond(f"The role: {rolename} does not exist, please try another role.")
        Database.permRoles(ctx.guild.id, self.client.id, rolename, role.id)
        await ctx.respond(f"{rolename} has been set as the permission role.")
        
def setup(client): 
    client.add_cog(ButtonRoles(client))