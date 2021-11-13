import discord
from discord.ext import commands
from dotenv import load_dotenv
import os.path
import re
import grapheme
import tweepy

intents = discord.Intents.default()
intents.messages = True

kt_bot = commands.Bot(command_prefix="%", intents=intents, help_command=commands.DefaultHelpCommand(
    no_category='Commands'
))
load_dotenv()
KT_TOKEN = os.getenv('KT_TOKEN')
MAX_HAND_SETS = 2
server_max_hands = {}
server_recent_tat = {}

PREFIXES = "$!%"

TWT_API_KEY = os.getenv("TWT_API_KEY")
TWT_API_SECRET = os.getenv("TWT_API_SECRET")
TWT_BEARER_TOKEN = os.getenv("TWT_BEARER_TOKEN")
TWT_ACCESS_TOKEN = os.getenv("TWT_ACCESS_TOKEN")
TWT_ACCESS_SECRET = os.getenv("TWT_ACCESS_SECRET")
tw_auth = tweepy.OAuthHandler(TWT_API_KEY, TWT_API_SECRET)
tw_auth.set_access_token(TWT_ACCESS_TOKEN, TWT_ACCESS_SECRET)
api = tweepy.API(tw_auth)

api.verify_credentials()


@kt_bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return
    guildID = message.guild.id
    if guildID not in server_max_hands.keys():
        server_max_hands[message.guild.id] = MAX_HAND_SETS
    if message.content[0] in PREFIXES:
        await kt_bot.process_commands(message)
        return
    wws = re.sub(r'\s', '', message.content)
    length = grapheme.length(wws)
    if length > 0 and length % 8 == 0 and length // 8 <= server_max_hands[guildID]:
        out = ""
        for i in range(0, length, 8):
            out += f"{grapheme.slice(wws, i, i + 4)} {grapheme.slice(wws, i + 4, i + 8)}\n".upper()
        await message.channel.send(out)
        set_recent(message, out)


@kt_bot.command(name="knuc_max", help='owner uses to change max number of hand sets',
             usage='(num_hand_sets) to change max number of hand sets, no parameters to check current max')
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
            await ctx.send("invalid number of hands")
    except ValueError:
        await ctx.send("invalid number of hands")


@kt_bot.command(name="tweet", help='people with "knuc tats login" role use to tweet most recent tat',
             usage='to tweet most recent tat in channel, -s to skip confirmation')
@commands.has_role("knuc tats login")
async def tweet(ctx, *args):
    to_tweet = server_recent_tat[ctx.guild.id][ctx.channel.id]
    if "-s" not in args:
        await ctx.send(f"You want to tweet this? (y/n)\n>>> {to_tweet}")
        msg = (await kt_bot.wait_for('message', check=lambda
            message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
    else:
        msg = 'y'
    if msg.lower() in ['y', 'yes']:
        try:
            response = api.update_status(to_tweet)
            await ctx.send(f"Tweet successful!\nhttps://twitter.com/uvmknuctats/status/{response.id_str}")
        except tweepy.TweepyException as e:
            print(e)
            await ctx.send(f"Tweet failed. Error code: {e}")
    else:
        await ctx.send("Tweet cancelled.")

@kt_bot.event
async def on_ready():
    print("ready!")

def set_recent(message, tats):
    if message.guild.id not in server_recent_tat.keys():
        server_recent_tat[message.guild.id] = {}
    server_recent_tat[message.guild.id][message.channel.id] = tats


kt_bot.run(KT_TOKEN)
