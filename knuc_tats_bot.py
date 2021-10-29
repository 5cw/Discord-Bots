import discord
from discord.ext import commands
from dotenv import load_dotenv
import os.path
import re
intents = discord.Intents.default()
intents.messages = True

kt_bot = commands.Bot(command_prefix="KT_BOT", intents=intents)
load_dotenv()
KT_TOKEN = os.getenv('KT_TOKEN')

@kt_bot.event
async def on_message(message):
    if message.author == kt_bot.user:
        return
    m = re.match(r'^(.{4}) ?(.{4})$', message.content)
    if m:
        await message.channel.send(f"{m.group(1).upper()} {m.group(2).upper()}")

@kt_bot.event
async def on_ready():
    print("ready!")

kt_bot.run(KT_TOKEN)