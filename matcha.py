import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import os

load_dotenv()

# Bot configuration
CHANNEL_ID =  int(os.getenv('CHANNEL_ID'))
BOT_TOKEN =  os.getenv('BOT_TOKEN')

# URL config
base_url = "https://www.matchajp.net/"
add_url = "collections/"
endpoints = ["yomo-no-kaori", "samidori", "matsukaze"]

urls = [base_url + add_url + endpoint for endpoint in endpoints]

def scrape_matcha(url):
    results = []
    # Send HTTP request
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    items = soup.select('.card, .card--standard, .card--media + div + div')

    for item in items:
        sold_out = item.select_one('.card__badge')
        title = item.select_one('.card__heading')
        link = title.select_one('a')['href']
        price = item.select_one('.price-item, .price-item--regular')

        title_result = title.get_text().strip() if title else "No title found"
        price_result = price.get_text().strip() if price else "No Price"
        sold_out_result = sold_out.get_text().strip() if sold_out else "No sold out data"
        sold_out_result = sold_out_result if sold_out_result != "" else "In Stock"
        availability_flag = 1 if sold_out_result == 'In Stock' else 0

        result = {'title': title_result, 'price': price_result, 'sold_out': sold_out_result, 'link': link, 'availability_flag': availability_flag}
        results.append(result)

    return results

# Set up the bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Background task to scrape every 30 minutes
@tasks.loop(minutes=30)
async def auto_scrape():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel with ID {CHANNEL_ID} not found")
        return

    try:
        for i, url in enumerate(urls):
        # Send HTTP request
            results = scrape_matcha(url)

            embed=discord.Embed(
                title="In Stock Alert" if any([item['availability_flag'] for item in results]) else "All Sold Out",
                color=discord.Color.green(),
            )

            embed.add_field(name='\u200b', value=f"[{endpoints[i]}]({url})", inline=False)

            for item in results:
                embed.add_field(name=item['title'], value=f"> Price: [{item['price']}]({base_url + item['link']}) \n> Availability: {item['sold_out']}", inline=False)

            # Send result to the specified channel
            await channel.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await channel.send(f"Auto-scrape error: {str(e)}")
    except Exception as e:
        await channel.send(f"Auto-scrape failed: {str(e)}")

# Ensure the bot is ready before starting the task
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not auto_scrape.is_running():
        auto_scrape.start()  # Start the background task

# Command: Manual scrape (same as before)
@bot.command()
async def scrape(ctx, url: str):
    # Validate URL
    if not re.match(r'^https?://', url):
        await ctx.send("Please provide a valid URL starting with http:// or https://")
        return

    try:
        # Send HTTP request
        results = scrape_matcha(url)

        embed=discord.Embed(
            title="Matcha Checkup",
            color=discord.Color.green(),
        )

        for item in results:
            embed.add_field(name=item['title'], value=f"> Price: {item['price']} \n> Availability: {item['sold_out']}", inline=False)
    
        # Send result to Discord
        await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Error fetching the page: {str(e)}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Run the bot
bot.run(BOT_TOKEN)