import discord
from discord.ext import commands
import requests
import random
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG)

intents = discord.Intents.all()

# Read the token from the file
with open('token', 'r') as f:
    TOKEN = f.read().strip()

bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'We have logged in as {bot.user}')

@bot.command()
async def yuri(ctx, *tags):
    base_tags = ['yuri'] + list(tags)
    tags_str = '+'.join(base_tags)
    url = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags={tags_str}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad response status
        
        if len(response.text) < 5:  # Check if response text is too short (usually "{}")
            await ctx.send("404 Tag not found or invalid response from the server.")
            return
        
        data = response.json()
        
        if not data:
            await ctx.send("No images found with the provided tags.")
            return
        
        index = random.randint(0, len(data) - 1)
        
        image_data = data[index]
        directory = image_data["directory"]
        file_url = image_data["image"]
        image_url = f"https://safebooru.org/images/{directory}/{file_url}"
        image_source = f"https://safebooru.org/index.php?page=post&s=view&id={image_data['id']}"
        
        embed = discord.Embed()
        embed.set_image(url=image_url)
        embed.set_author(name="Image Source", url=image_source)
        
        message = await ctx.send(embed=embed)
        
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id
        
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
                
                if str(reaction.emoji) == "◀️":
                    index = (index - 1) % len(data)
                elif str(reaction.emoji) == "▶️":
                    index = (index + 1) % len(data)
                
                image_data = data[index]
                directory = image_data["directory"]
                file_url = image_data["image"]
                image_url = f"https://safebooru.org/images/{directory}/{file_url}"
                image_source = f"https://safebooru.org/index.php?page=post&s=view&id={image_data['id']}"
                
                embed = discord.Embed()
                embed.set_image(url=image_url)
                embed.set_author(name="Original Page", url=image_source)
                
                await message.edit(embed=embed)
                await message.remove_reaction(reaction, user)
                
            except asyncio.TimeoutError:
                break
    
    except requests.exceptions.HTTPError as http_err:
        await ctx.send(f'HTTP error occurred: {http_err}')
        logging.error(f'HTTP error occurred: {http_err}')
    except requests.exceptions.RequestException as req_err:
        await ctx.send(f'Request exception occurred: {req_err}')
        logging.error(f'Request exception occurred: {req_err}')
    except Exception as e:
        await ctx.send('An unexpected error occurred.')
        logging.error(f'An unexpected error occurred: {e}')


bot.run(TOKEN)
