import discord
from discord.ext import commands
from dotenv import load_dotenv
import os.path
import re
import grapheme
import tweepy
intents = discord.Intents.default()
intents.messages = True

kt_bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
load_dotenv()
KT_TOKEN = os.getenv('KT_TOKEN')
MAX_HAND_SETS = 2
server_max_hands = {}

PREFIXES = "$!"


@kt_bot.event
async def on_message(message):
    if message.guild is None:
        return
    guildID = message.guild.id
    if guildID not in server_max_hands.keys():
        server_max_hands[message.guild.id] = MAX_HAND_SETS
    if message.author.bot or message.content[0] in PREFIXES:
        await kt_bot.process_commands(message)
        return

    print(message.content)
    wws = re.sub(r'\s', '', message.content)
    length = grapheme.length(wws)
    if length > 0 and length % 8 == 0 and length // 8 <= server_max_hands[guildID]:
        out = ""
        for i in range(0,length,8):
            out += f"{grapheme.slice(wws, i, i+4)} {grapheme.slice(wws, i+4, i+8)}\n".upper()
        await message.channel.send(out)

@kt_bot.command(name="knuc_max")
@commands.is_owner()
async def max(ctx, *args):
    global MAX_HAND_SETS
    if len(args) == 0:
        await ctx.send(f"Maximum sets of hands is currently {server_max_hands[ctx.guild.id]}")
        return
    try:
        amount = int(args[0])
        if 0 < amount < 100:
            server_max_hands[ctx.guild.id] = amount
            await ctx.send(f"Maximum sets of hands changed to {amount}")
        else:
            await ctx.send("invalid")
    except ValueError:
        await ctx.send("invalid")



@kt_bot.event
async def on_ready():
    print("ready!")

kt_bot.run(KT_TOKEN)