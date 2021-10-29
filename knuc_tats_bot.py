import discord
from discord.ext import commands
from dotenv import load_dotenv
import os.path
import re
intents = discord.Intents.default()
intents.messages = True

kt_bot = commands.Bot(command_prefix="KT_BOT!", intents=intents, help_command=None)
load_dotenv()
KT_TOKEN = os.getenv('KT_TOKEN')
MAX_HAND_SETS = 2

@kt_bot.event
async def on_message(message):
    if message.author == kt_bot.user:
        return

    wws = re.sub(r'\s', '', message.content)
    if len(wws) > 0 and len(wws) % 8 == 0 and len(wws) // 8 <= MAX_HAND_SETS:
        out = ""
        for i in range(0,len(wws),8):
            out += f"{wws[i:i+4]} {wws[i+4:i+8]}\n".upper()
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