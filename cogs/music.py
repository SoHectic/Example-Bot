import re
import discord
import lavalink
import math
import random
import logging

from utils.Database import Database
from utils.Logger import Logger
from asyncio import sleep
from discord import ApplicationContext
from discord.colour import Colour
from discord.commands import slash_command, Option
from discord.ext import commands
from lavalink.events import Event, TrackStartEvent
from lavalink.models import BasePlayer
from datetime import datetime, timedelta

url_rx = re.compile(r'https?://(?:www\.)?.+')
time_rx = re.compile('[0-9]+')
url_rx = re.compile(r'https?://(?:www\.)?.+')
logger = logging.getLogger('livebot')
guild_ids = []

class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                    'localhost', 
                    7000, 
                    'youshallnotpass', 
                    'us', 
                    'default-node', 
                    120, 
                    "test-node", 
                    5
            )
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_SERVER_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_STATE_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the client to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id, region= "us")
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the 
        # disconnect
        player.channel_id = None
        self.cleanup()

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

        lavalink.add_event_hook(self.track_hook)
        lavalink.add_event_hook(self.song_stuck)
        lavalink.add_event_hook(self.new_song)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.client.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the client and command author share a mutual voicechannel.

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            #await ctx.send(error.original)
            logger.warning(error.original)

            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    async def ensure_voice(self, ctx):
        """ This check ensures that the client and command author are in the same voicechannel. """
        player = self.client.lavalink.player_manager.create(ctx.guild_id, endpoint=str("us_east"))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the client to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the client to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play', 'qload', 'tongo', 'ctest')

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            logger.warning("User is not in a voice channel when using a music command")
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not should_connect:
                logger.warning("Used music command while the bot was not connected")
                raise commands.CommandInvokeError('Not connected.')
                
            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                logger.warning("Bot needs the connect and speak permissions")
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')
                

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                logger.warning("User did not run the music command from the same voice channel as the bot")
                raise commands.CommandInvokeError('You need to be in my voicechannel.')
    
    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the client to disconnect from the voicechannel.
            guild_id = int(event.player.guild_id)
            guild = self.client.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

    async def song_stuck(self, event):
        if isinstance(event, lavalink.events.TrackStuckEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)
            logger.warning("The song was stuck so I left the channel.")

    async def new_song(self, event):
        if isinstance(event, lavalink.events.TrackStartEvent):
            
            channel = self.client.get_channel(event.player.channel_id)
            randColour = random.randint(0, 0xffffff)
            embed = discord.Embed(
                    title='Now Playing:',
                    description=f'**[{event.player.current.title}]({event.player.current.uri})**',
                    colour=randColour
                )

            embed.set_image(url=f"https://img.youtube.com/vi/{event.player.current.identifier}/0.jpg")
            embed.set_footer(text=f"0:00 / {lavalink.utils.format_time(event.player.current.duration).lstrip('0:')}")

            await channel.send(embed=embed)
                
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Music Loaded")

        if not hasattr(self.client, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            self.client.lavalink = lavalink.Client(self.client.user.id)
            self.client.lavalink.add_node('localhost', 7000, 'youshallnotpass', 'us', 'default-node', 120, "test-node", 5)  # Host, Port, Password, Region, resume key, resume timeout, name, resume attempts

    @slash_command(description="Used to play, queue, or resume a song.", guild_ids=guild_ids)
    @commands.has_any_role("DJ")
    async def play(self, ctx: ApplicationContext, *, query: Option(str, "The song you want to play", default="resume")):
        """ Searches and plays a song from a given query. """
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(color=randColour)
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if query == "resume":
            if player.is_connected and player.paused:
                await player.set_pause(False)
                embed.title = "Resumed!"
                return await ctx.respond(embed=embed, ephemeral=True)

        query = query.strip('<>')

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.respond('Nothing found!', ephemeral=True)

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                player.add(requester=ctx.author.id, track=track)

            embed.title = 'Now Playing:'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
        elif player.is_playing:
            track = results['tracks'][0]
            randColour = random.randint(0, 0xffffff)
            embed.title = 'Queued:'
            embed.description=f'[{track["info"]["title"]}]({track["info"]["uri"]})'

            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
        else:
            track = results['tracks'][0]
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
            embed.title=f"Now Playing"
            embed.description = "All songs will be displayed in the voice channel text chat."

        if not player.is_playing:
            await player.set_volume(5)
            await player.play()
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @slash_command(description="Used to stop the play of a song", guild_ids=guild_ids)
    @commands.has_any_role("DJ")
    async def stop(self, ctx: ApplicationContext):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.respond('Not connected.', ephemeral=True)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the client
            # may not disconnect the client.
            return await ctx.respond('You\'re not in my voicechannel!', ephemeral=True)

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)

        await ctx.respond('*⃣ | Disconnected.', delete_after=2, ephemeral=True)

    @slash_command(description="Used to show the current queue of songs", guild_ids=guild_ids)
    @commands.has_any_role("DJ")
    async def queue(self, ctx: ApplicationContext, page: Option(int, "Page Number", default=1)):
        await ctx.defer()
        if isinstance(page, str):
            await ctx.respond('You must either use `queue` or `queue (page number)`', delete_after=2)
            return

        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_playing:
            return await ctx.respond('Nothing is playing and the queue is empty.')
        
        if not player.queue:
            return await ctx.respond('There is nothing in the queue.')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue_list = ''

        for i, track in enumerate(player.queue[start:end], start=start):
            queue_list += f'`{i + 1}.`[**{track.title}**]({track.uri})\n'
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(
            title=f'Songs in Current Queue: {len(player.queue)}',
            description=f'{queue_list}\n',
            colour=randColour
        )
        embed.set_footer(text=f'Viewing Page: {page}/{pages}')
        await ctx.respond(embed=embed)

    @slash_command(description="Shows the current song playing and the current position in the song", guild_ids=guild_ids)
    @commands.has_any_role("DJ")
    async def now(self, ctx: ApplicationContext):
        await ctx.defer()
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        song = 'Nothing'
        if player.current:
            pos = lavalink.utils.format_time(player.position)[3:]
            if player.current.stream:
                dur = 'LIVE'
            else:
                dur = lavalink.utils.format_time(player.current.duration)[3:]

            song = f'**[{player.current.title}]({player.current.uri})**\n({pos}/{dur})'
        
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(
            title='Now Playing:',
            description=song,
            colour=randColour
        )

        embed.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/0.jpg")
        await ctx.respond(embed=embed)

    @slash_command(description="Skips the currently playing song", guild_ids=guild_ids)
    @commands.has_any_role("DJ")
    async def skip(self, ctx: ApplicationContext):
        await ctx.defer()
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_playing:
            return await ctx.respond('Nothing is playing.', ephemeral=True)
        else:
            await ctx.respond('Skipping', ephemeral=True)
            await player.skip()

    @slash_command(description="Pauses the currently playing song", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def pause(self, ctx: ApplicationContext):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not player.is_playing:
            return await ctx.respond('Not playing anything.', ephemeral=True)
        
        if not player.paused:
            await player.set_pause(True)
            await ctx.respond('Paused', ephemeral=True)

    @slash_command(description="resumes the currently paused song", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def resume(self, ctx: ApplicationContext):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not player.paused:
            await ctx.respond('There is nothing paused.', ephemeral=True)
        
        if player.paused:
            await player.set_pause(False)
            await ctx.respond('Resumed.', ephemeral=True)

    @slash_command(description="Clears the current song queue", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def clearq(self, ctx: ApplicationContext):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not player.queue:
            return await ctx.respond('Nothing in Queue.', ephemeral=True)
        else:
            player.queue.clear()
            await ctx.respond('Queue has been cleared.', ephemeral=True)

    @slash_command(description="Changes the volume of the player", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def volume(self, ctx: ApplicationContext, volume: Option(int, "Volume to set", default=None)):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not volume:
            return await ctx.respond(f'{player.volume}')

        await player.set_volume(volume)
        await ctx.respond(f'The volume is now: {player.volume}%')
        
    @slash_command(description="Turns repeat on or off", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def repeat(self, ctx: ApplicationContext):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not player.is_playing:
            return await ctx.respond('Nothing is playing.')

        player.repeat = not player.repeat

        await ctx.respond('`Repeat ' + ('enabled`' if player.repeat else 'disabled`'))

    @slash_command(description="Turns on shuffle for the current queue", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def shuffle(self, ctx: ApplicationContext):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        await ctx.defer()
        if not player.is_playing:
            return await ctx.respond('There is nothing playing.')

        player.shuffle = not player.shuffle
        await ctx.respond(f'`Shuffle ' + ('enabled`' if player.shuffle else 'disabled`'))
    
    @slash_command(description="Used to remove the specified song", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def remove(self, ctx: ApplicationContext, index: Option(int, "Song to remove")):
        await ctx.defer()
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        
        if not player.queue:
            return await ctx.respond('`Nothing Queued.`')

        if index > len(player.queue) or index < 1:
            return await ctx.respond('Song number has to be >=1 and <= the queue size')

        index = index - 1
        removed = player.queue.pop(index)

        await ctx.respond('`Removed **' + removed.title + '** from the queue`')

    @slash_command(description="Used to seek ahead or back in the currently playing song", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def seek(self, ctx: ApplicationContext, time: Option(int, "Time in seconds to seek forward")):
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(color=randColour)
        await ctx.defer()
        
        if not player.is_playing:
            embed.title = 'There is nothing playing.'
        else:
            pos = '+'
            if time.startswith('-'):
                pos = '-'
            else:
                seconds = time_rx.search(time)
                seconds = int(seconds.group()) * 1000
                track_time = player.position + seconds
                await player.seek(track_time)
                embed.title = f'Moved track to: `{lavalink.utils.format_time(track_time)[3:]}`'
        await ctx.respond(embed=embed)

    @slash_command(description="Loads the Tongo playlist", guild_ids=guild_ids)
    @commands.has_role("DJ")
    async def tongo(self, ctx):
        await ctx.defer()
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        results = Database.load(f'tongo-{self.client.user.id}', "queues")
        query = results[0]['song']
        qList = []
        i = 1
        x = 0

        if not url_rx.match(query):
            query = f'ytsearch:{query}'
        result = await player.node.get_tracks(query)
        if not result or not result['tracks']:
            return await ctx.respond("Nothing found!", ephemeral=True)
        
        track = result['tracks'][0]
        track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
        player.add(requester=ctx.author.id, track=track)

        if not player.is_playing:
            await player.set_volume(5)
            await player.play()
            await ctx.respond(f"Loaded first song. Loading the rest of: `Tongo`.", ephemeral=True)
        else:
            await ctx.respond(f'`Tongo` was loaded into the queue.', ephemeral=True)

        while i < len(results):
            qList.append(results[i]['song'])
            i += 1

        while x < len(qList):
            query = qList[x]
            if not url_rx.match(query):
                query = f'ytsearch:{query}'
            result = await player.node.get_tracks(query)
            if not result or not result['tracks']:
                return await ctx.send('Nothing found!')
            track = result['tracks'][0]
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
            x += 1

    @slash_command(description="Loads the specified queue")
    @commands.has_role("DJ")
    async def qload(self, ctx, queue: Option(str, "The queue name")):
        await ctx.defer()
        if queue == None:
            await ctx.respond("You must put in a queue name to load. use the `queues` command to see a list.", ephemeral=True)
            logger.warning("Someone failed to add a queue name when using qload.")
            return

        tableName = f"{queue}-{self.client.user.id}"
        player = self.client.lavalink.player_manager.get(ctx.guild_id)
        results = Database.load(tableName, "queues")
        query = results[0]['song']
        qList = []
        i = 1
        x = 0

        if not url_rx.match(query):
            query = f'ytsearch:{query}'
        result = await player.node.get_tracks(query)
        if not result or not result['tracks']:
            return await ctx.respond("Nothing found!", ephemeral=True)
        
        track = result['tracks'][0]
        track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
        player.add(requester=ctx.author.id, track=track)

        if not player.is_playing:
            await player.set_volume(5)
            await player.play()
            player.shuffle = not player.shuffle
            await ctx.respond(f"Loaded first song. Loading the rest of: `{queue}`.", ephemeral=True)
        else:
            await ctx.respond(f'`{queue}` was loaded into the queue.', ephemeral=True)

        while i < len(results):
            qList.append(results[i]['song'])
            i += 1

        while x < len(qList):
            query = qList[x]
            if not url_rx.match(query):
                query = f'ytsearch:{query}'
            result = await player.node.get_tracks(query)
            if not result or not result['tracks']:
                return await ctx.respond('Nothing found!', ephemeral=True)
            track = result['tracks'][0]
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
            x += 1

    @slash_command(description="used to test what channel IDs the command is used from")
    async def ctest(self, ctx: ApplicationContext):
        print(ctx.channel_id)
        await ctx.respond('printed')

def setup(client):
    client.add_cog(Music(client))