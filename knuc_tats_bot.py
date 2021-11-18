import discord
from discord.ext import commands
from dotenv import load_dotenv
from time import time
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
server_disabled = {}

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


KNUC_ADMIN_ROLES = [821184954116341780, 693144828590162030]

@kt_bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return
    guildID = message.guild.id
    if guildID not in server_max_hands.keys():
        server_max_hands[message.guild.id] = MAX_HAND_SETS
    if len(message.content) < 1:
        print(f"empty message with id {message.id}")
        return
    if message.content[0] in PREFIXES:
        await kt_bot.process_commands(message)
        return
    if time_left(message.guild.id, message.guild.id) is not None or \
            time_left(message.guild.id, message.channel.id) is not None:
        return
    wws = re.sub(r'\s', '', message.content)
    length = grapheme.length(wws)
    if length > 0 and length % 8 == 0 and length // 8 <= server_max_hands[guildID]:
        out = ""
        for i in range(0, length, 8):
            out += f"{grapheme.slice(wws, i, i + 4)} {grapheme.slice(wws, i + 4, i + 8)}\n".upper()
        await message.channel.send(out)
        set_recent(message, out)


@kt_bot.command(name="max", help='owner uses to change max number of hand sets',
             usage='(num_hand_sets) to change max number of hand sets, no parameters to check current max')
@commands.is_owner()
async def max(ctx, *args):
    if len(args) == 0:
        await ctx.send(f"Maximum sets of hands is currently {server_max_hands[ctx.guild.id]}."
                       f"{looks_like(server_max_hands[ctx.guild.id])}")
        return
    try:
        amount = int(args[0])
        if 0 < amount < 100:
            server_max_hands[ctx.guild.id] = amount
            await ctx.send(f"Maximum sets of hands changed to {amount}.{looks_like(amount)}")
        else:
            await ctx.send("invalid number of hands")
    except ValueError:
        await ctx.send("invalid number of hands")


@kt_bot.command(name="mute", help='mute bot in channel or server wide for period of time or until unmuted',
             usage='(minutes) to mute for a number of minutes. -server to mute server-wide, -stop to unmute, -check to see how long it is muted for.')
@commands.has_role("knuc tats login")
async def mute(ctx, *args):
    admin = False
    for role in ctx.author.roles:
        if role.id in KNUC_ADMIN_ROLES:
            admin = True
            break

    args = list(args)
    try:
        args.remove("-check")
        check = True
    except ValueError:
        check = False
    try:
        args.remove("-server")
        server = True
    except ValueError:
        server = False
    try:
        args.remove("-stop")
        stop = True
    except ValueError:
        stop = False

    try:
        amount = float(args[0])
        if amount < 0 or amount > 60 * 24 * 30:
            raise ValueError
    except IndexError:
        amount = -1
    except ValueError:
        await ctx.send("Invalid number of minutes.")
        return

    if not server:
        ID = ctx.channel.id
    else:
        ID = ctx.guild.id

    curr = time()

    left = time_left(ctx.guild.id, ID)
    s_left = time_left(ctx.guild.id, ctx.guild.id)


    if check and stop:
        await ctx.send("Cannot both check and stop mute.")

    entity = ctx.guild.name if server else f"<#{ctx.channel.id}>"

    if left is None and (check or stop):
        if s_left is None:
            await ctx.send(f"{entity} is not muted.")
            return
        else:
            left = s_left
            entity = ctx.guild.name
            server = True

    if check:
        if left < 0:
            await ctx.send(f"{entity} is muted indefinitely")
            return
        left = int(left)
        m = left // 60
        s = left % 60
        await ctx.send(f"{entity} "
                       f"is muted for {m} more minutes" + (f" and {s} more seconds." if s != 0 else "."))
        return

    if not admin:
        await ctx.send("You do not have permissions to mute.")
        return

    if stop:
        if server:
            server_disabled[ctx.guild.id].clear()
        else:
            del server_disabled[ctx.guild.id][ctx.channel.id]
        await ctx.send(f"{entity} has been unmuted.")
        return

    if amount > 0:
        until = curr + (amount * 60)
    else:
        until = -1

    server_disabled[ctx.guild.id][ID] = until

    if amount < 0:
        await ctx.send(f"{entity} has been muted indefinitely")
        return

    amount = int(amount * 60)
    m = amount // 60
    s = amount % 60
    await ctx.send(f"{entity} "
                   f"has been muted for {m} minutes" + (f" and {s} seconds." if s != 0 else "."))



@kt_bot.command(name="tweet", help='people with "knuc tats login" role use to tweet most recent tat',
             usage='to tweet most recent tat in channel, -s to skip confirmation')
@commands.has_role("knuc tats login")
async def tweet(ctx, *args):
    try:
        to_tweet = server_recent_tat[ctx.guild.id][ctx.channel.id]
    except KeyError:
        await ctx.send("No knuc tats have been sent in this channel since the bot was last restarted.")
        return
    if len(to_tweet) > 240:
        await ctx.send("Too many characters to tweet.")
        return
    if "-s" not in args:
        await ctx.send(f"You want to tweet this? (y/n)\n>>> {to_tweet}")
        confirm = (await kt_bot.wait_for('message', check=lambda
            message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
    else:
        confirm = 'y'
    if confirm and confirm.lower()[0] == 'y':
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

def looks_like(amount):
    out = "\nThis is what that looks like:\n>>> "
    out += "HAND SETS\n" * amount
    return out


def time_left(guildID, ID):
    if guildID not in server_disabled.keys():
        server_disabled[guildID] = {}

    print(server_disabled)
    if ID not in server_disabled[guildID].keys():
        return None
    curr = time()
    until = server_disabled[guildID][ID]
    if until > 0:
        left = until - curr
        print(left)
        if left <= 0:
            del server_disabled[guildID][ID]
            return None
        return left
    else:
        return -1
kt_bot.run(KT_TOKEN)
