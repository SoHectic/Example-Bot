import discord
import random
import logging
import requests
import json
from discord import ApplicationContext
from discord.ext import commands
from discord.commands import slash_command, SlashCommandGroup, Option
from utils.Logger import Logger

logger = logging.getLogger('livebot')

class Tarkov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_users = ()

    guild_ids = []

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Tarkov Loaded')

    @slash_command(description="Shows useful Tarkov information", guild_ids=guild_ids)
    async def tarkovinfo(self, ctx: ApplicationContext):
        randColour = random.randint(0, 0xffffff)
        e = discord.Embed(
                title= 'Tarkov Information Links',
                description= '',
                colour = randColour
            )
        
        e.add_field(name='Ammo Information: ', value='[Tarkov Ballistics](https://eft-ammo.com/nofoodaftermidnight)', inline=False)
        e.add_field(name='Hideout Items: ', value='[Tarkov Hideout Items](https://static.wikia.nocookie.net/escapefromtarkov_gamepedia/images/3/39/Hideout-Requirements-Items-to-Keep.jpg/revision/latest/scale-to-width-down/2212?cb=20210114214038)', inline=False)
        e.add_field(name='Task Items: ', value='[Tarkov Task Items](https://static.wikia.nocookie.net/escapefromtarkov_gamepedia/images/1/19/QuestItemRequirements.png/revision/latest/scale-to-width-down/4317?cb=20210212192637)', inline=False)
        e.add_field(name='Tarkov Wiki', value='[Wiki](https://escapefromtarkov.gamepedia.com/Escape_from_Tarkov_Wiki)', inline=False)

        await ctx.respond(embed=e)

    @slash_command(description="Gets the flea market value for the searched item.", guild_ids=guild_ids)
    async def price(self, ctx: ApplicationContext, item: Option(str, "Item you want pricing information about.")):
        await ctx.defer()
        query = '{' + f'itemsByName(name: "{item}")' + """
            {
                name
                iconLink
                basePrice
                sellFor{
                    price
                    source
                    currency
                }
            }
        }
        """
        
        response = requests.post('https://api.tarkov.dev/graphql', json={'query': query})
        print(response.text)        

        if response.status_code == 200:
            data = response.json()
            if data['data']['itemsByName'] == []:
                await ctx.respond('You need to be more specific with your search. Nothing was found.')
                return
        else:
            await ctx.respond('Could not find that Item, try being more specific or check spelling.')
            raise Exception("Query Failed to run by returning code of {}. {}".format(response.status_code, query))
            return

        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(color=randColour)

        name = data['data']['itemsByName'][0]['name']
        iconLink = data['data']['itemsByName'][0]['iconLink']
        sellFor = data['data']['itemsByName'][0]['sellFor']
        basePrice = data['data']['itemsByName'][0]['basePrice']
        flea = len(data['data']['itemsByName'][0]['sellFor']) - 1
        fleaPrice = data['data']['itemsByName'][0]['sellFor'][flea]['price']
        fleaCurrency = data['data']['itemsByName'][0]['sellFor'][flea]['currency']
        
        sortedPrices = sorted(sellFor, key=lambda x: x['price'], reverse=True)
        
        for i in range(len(sortedPrices)):
            if sortedPrices[i]['source'] == 'fleaMarket':
                del sortedPrices[i]
                break
        bestTrader = sortedPrices[0]['source']
        traderPrice = sortedPrices[0]['price']
        currency = sortedPrices[0]['currency']

        embed.title = name
        embed.set_thumbnail(url=iconLink)
        embed.description = f'Best Trader: `{bestTrader.capitalize()}`\n Trader Price: `{currency} {traderPrice}`\n Flea Market: `{fleaCurrency} {fleaPrice}`\n'

        await ctx.respond(embed=embed)

    @slash_command(description="A list of useful barters", guild_ids=guild_ids)
    async def barters(self, ctx: ApplicationContext):
        await ctx.defer()
        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(color=randColour)

        embed.title = f'Great Barters'
        embed.add_field(name='Dogtag Case (Jaeger LL1)', value='Requires `3` flash drives(<65K RUB) \nSells for 195K RUB to Therapist', inline=False)
        embed.add_field(name='Kiver Helmet (Ragman LL1)', value='Requires `2` Chainlets(<7.6K RUB) \nSells for 19,296 RUB to Ragman', inline=False)
        embed.add_field(name='Surv12 Kit (Jaeger LL2)', value='Requires `1` Vase (<42k RUB) \nSells for 45,360 RUB to Therapist', inline=False)
        embed.add_field(name='Alpha Dog Suppressor (Mechanic LL2)', value='Requires `2` White salt(<9.7K RUB) \nSells for 20,529 to Mechanic', inline=False)
        embed.add_field(name='Tarzan Rig (Jaeger LL2)', value='Requires `1` Hunting matches(<11.3K RUB) \nSells for 11,904 RUB to Ragman', inline=False)
        embed.add_field(name='Belt Rig (Ragman LL3)', value='Requires `1` Teapot(<33.9K RUB) \nSells for 34,164 RUB to Ragman', inline=False)
        embed.add_field(name='Mini Monster Suppressor (Skier LL2)', value='Requires `1` Video Cassette (<32K RUB) \nSells for 32,480 RUB to Mechanic', inline=False)

        await ctx.respond(embed=embed)

    @slash_command(description="Shows the current status of EFT servers", guild_ids=guild_ids)
    async def eftstatus(self, ctx: ApplicationContext):
        await ctx.defer()
        query = """
            {
                status{
                    currentStatuses{
                        name
                        message
                        status
                    }
                    messages{
                        time
                        type
                        content
                        solveTime
                    }
                }
            }
        """

        response = requests.post('https://api.tarkov.dev/graphql', json={'query': query})
        if response.status_code == 200:
            data = response.json()
        else:
            raise Exception("Query Failed to run by returning code of {}. {}".format(response.status_code, query))

        website = data['data']['status']['currentStatuses'][0]
        forum = data['data']['status']['currentStatuses'][1]
        auth = data['data']['status']['currentStatuses'][2]
        launcher = data['data']['status']['currentStatuses'][3]
        group = data['data']['status']['currentStatuses'][4]
        trading = data['data']['status']['currentStatuses'][5]
        matchmaking = data['data']['status']['currentStatuses'][6]
        friends = data['data']['status']['currentStatuses'][7]
        inventory = data['data']['status']['currentStatuses'][8]
        gbl = data['data']['status']['currentStatuses'][9] 

        

        randColour = random.randint(0, 0xffffff)
        embed = discord.Embed(color=randColour)
        embed.title = f"EFT Status"
        embed.description = f"""
            `0: OK`/`1: BAD`\n 
            Website: {website['status']}\n 
            Forum: {forum['status']}\n 
            Auth: {auth['status']}\n
            Launcher: {launcher['status']}\n
            Party:  {group['status']}\n
            """
        


        await ctx.respond(embed=embed)
    

def setup(bot):
    bot.add_cog(Tarkov(bot))
