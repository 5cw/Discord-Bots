import discord
from discord.ext import commands
from dotenv import load_dotenv
import os.path
import re
import grapheme
intents = discord.Intents.default()
intents.messages = True

kt_bot = commands.Bot(command_prefix="KT_BOT!", intents=intents, help_command=None)
load_dotenv()
KT_TOKEN = os.getenv('KT_TOKEN')
MAX_HAND_SETS = 2

PREFIXES = "$!"


@kt_bot.event
async def on_message(message):
    if message.author.bot or message.content[0] in PREFIXES:
        return

    print(message.content)
    wws = re.sub(r'\s', '', message.content)
    length = grapheme.length(wws)
    if length > 0 and length % 8 == 0 and length // 8 <= MAX_HAND_SETS:
        out = ""
        for i in range(0,length,8):
            out += f"{grapheme.slice(wws, i, i+4)} {grapheme.slice(wws, i+4, i+8)}\n".upper()
        await message.channel.send(out)

    await kt_bot.process_commands(message)

@kt_bot.command(name="max")
@commands.is_owner()
async def max(ctx, *args):
    global MAX_HAND_SETS
    if len(args) == 0:
        await ctx.send(f"Maximum sets of hands is currently {MAX_HAND_SETS}")
        return
    try:
        amount = int(args[0])
        if 0 < amount < 100:
            MAX_HAND_SETS = amount
            await ctx.send(f"Maximum sets of hands changed to {amount}")
        else:
            await ctx.send("invalid")
    except ValueError:
        await ctx.send("invalid")

@kt_bot.event
async def on_ready():
    print("ready!")

kt_bot.run(KT_TOKEN)