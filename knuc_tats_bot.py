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
KT_TOKEN = os.environ['KT_TOKEN']
MAX_HAND_SETS = 2
server_max_hands = {}
server_recent_tat = {}
server_disabled = {}

PREFIXES = "$!%"

TWT_API_KEY = os.environ["TWT_API_KEY"]
TWT_API_SECRET = os.environ["TWT_API_SECRET"]
TWT_BEARER_TOKEN = os.environ["TWT_BEARER_TOKEN"]
TWT_ACCESS_TOKEN = os.environ["TWT_ACCESS_TOKEN"]
TWT_ACCESS_SECRET = os.environ["TWT_ACCESS_SECRET"]
tw_auth = tweepy.OAuthHandler(TWT_API_KEY, TWT_API_SECRET)
tw_auth.set_access_token(TWT_ACCESS_TOKEN, TWT_ACCESS_SECRET)
api = tweepy.API(tw_auth)

api.verify_credentials()

KNUC_TATS_LOGIN_USERS = [999999999999999999, 999999999999999999, 999999999999999999, 999999999999999999]

time_dict = {
    's': 1,
    'm': 60
}
time_dict['h'] = 60 * time_dict['m']
time_dict['d'] = 24 * time_dict['h']
time_dict['w'] = 7 * time_dict['d']
time_dict['y'] = 365 * time_dict['d']

THOUSAND_YEARS_IN_SECS = time_dict["y"] * 1000


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
                usage='(num_hand_sets) to change max number of hand sets, no parameters to check current max. '
                      'Only members with permissions to manage server may use.')
@commands.has_permissions(manage_guild=True)
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
                usage='(minutes) or %mute #y#w#d#h#m#s, '
                      'leave blank to mute indefinitely. -server to mute server-wide, '
                      '-stop to unmute, -check to see how long a channel or server is muted for. '
                      'Only people with permission to manage channels may use this command.')
async def mute(ctx, *args):
    admin = ctx.author.guild_permissions.manage_channels
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

    amount = to_seconds("".join(args))
    if amount is None:
        await ctx.send("invalid amount of time.")
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
            await ctx.send(f"{entity} is muted indefinitely. %mute -stop to unmute.")
            return

        await ctx.send(f"{entity} will be muted for {time_string(int(left))} longer.")
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
        until = curr + amount
    else:
        until = -1

    server_disabled[ctx.guild.id][ID] = until

    if amount < 0:
        await ctx.send(f"{entity} has been muted indefinitely. %mute -stop to unmute.")
        return

    await ctx.send(f"{entity} has been muted for {time_string(amount)}.")


@kt_bot.command(name="tweet", help='people with "knuc tats login" role use to tweet most recent tat',
                usage='to tweet most recent tat in channel, -s to skip confirmation. '
                      'Only users known to have twitter login may use. '
                      'User IDs are hardcoded into bot, check with lexi if you want your discord ID added.')
async def tweet(ctx, *args):
    if ctx.author.id not in KNUC_TATS_LOGIN_USERS:
        return
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


def set_recent(message: discord.Message, tats: str):
    if message.guild.id not in server_recent_tat.keys():
        server_recent_tat[message.guild.id] = {}
    server_recent_tat[message.guild.id][message.channel.id] = tats


def looks_like(amount: int):
    out = "\nThis is what that looks like:\n>>> "
    out += "HAND SETS\n" * amount
    return out


def time_left(guildID: int, ID: int):
    if guildID not in server_disabled.keys():
        server_disabled[guildID] = {}
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


def time_string(seconds: int):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365)
    weeks, days = divmod(days, 7)
    segments = []
    if years > 0:
        segments.append(f"{years} year" + ("s" if years > 1 else ""))
    if weeks > 0:
        segments.append(f"{weeks} week" + ("s" if weeks > 1 else ""))
    if days > 0:
        segments.append(f"{days} day" + ("s" if days > 1 else ""))
    if hours > 0:
        segments.append(f"{hours} hour" + ("s" if hours > 1 else ""))
    if minutes > 0:
        segments.append(f"{minutes} minute" + ("s" if minutes > 1 else ""))
    if seconds > 0 or len(segments) == 0:
        segments.append(f"{seconds} second" + ("s" if seconds > 1 else ""))

    out = ""
    for i in segments[:-1]:
        out += i + ", "
    if len(segments) > 1:
        out += "and "
    out += segments[-1]
    return out


def to_seconds(parse: str) -> int:
    if parse == "":
        return -1
    try:
        out = float(parse)
    except ValueError:
        cleaned = re.sub(r'\s|,|and|for|\.', '', parse).lower()
        print(cleaned)
        out = 0
        for m in re.finditer(r"([-+]?\d*\.?\d*)"
                             r"(y(?:ears?)?|w(?:eeks?)?|d(?:ays?)?|h(?:ours?)?|m(?:inutes?)?|s(?:econds?)?)",
                             cleaned):
            out += float(m.group(1)) * time_dict[m.group(2)[0]]
    out = int(out)
    if out <= 0 or out >= THOUSAND_YEARS_IN_SECS:
        return None
    return out


kt_bot.run(KT_TOKEN)
