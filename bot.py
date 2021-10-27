import re
import time

import gspread

startTime = time.time()

import discord
from discord.ext import commands
from dotenv import load_dotenv
from decimal import *
import asyncio

import os.path

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='$', intents=intents, help_command=commands.DefaultHelpCommand(
    no_category='Commands'
))

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
"""
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name('cool-dollars-687de25f7d88.json', SCOPES)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
"""
# creds = ServiceAccountCredentials.from_json_keyfile_name('cool-dollars-687de25f7d88.json', SCOPES)
gc = gspread.service_account(filename='cool-dollars-687de25f7d88.json', scopes=[
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
])
sh = gc.open_by_key(SPREADSHEET_ID)


def fetchCache():
    global cache
    batch_get = sh.values_batch_get(["Balances!A:B", "bts!A:A", "bts!B:B"], {"majorDimension": "COLUMNS"})[
        "valueRanges"]
    cache = {}
    ids = batch_get[1].get('values') or [[]]
    cache["ids"] = [int(id) for id in ids[0]]
    name_bals = batch_get[0].get('values') or [[],[]]
    cache["names"] = name_bals[0]
    cache["balances"] = [Decimal(num) for num in name_bals[1]]
    banned = batch_get[2].get('values') or [[]]
    cache["banned"] = [int(id) for id in banned[0]]
    cache["user_locks"] = {i: asyncio.Lock() for i in cache["ids"]}


def pushCache(ban=False, unban=False):
    global cache
    data = []
    names = cache["names"]
    balances = [f"{bal:.2f}" for bal in cache["balances"]]
    ids = [str(id) for id in cache["ids"]]
    banned = [str(id) for id in cache["banned"]]
    if len(ids) > 0:
        data.append({
            'range': f"Balances!A1:B{len(ids)}",
            "majorDimension": "COLUMNS",
            "values": [names, balances]
        })
        data.append({
            'range': f"bts!A1:A{len(ids)}",
            "majorDimension": "COLUMNS",
            "values": [ids]
        })
    if len(banned) > 0:
        data.append({
            'range': f"bts!B1:B{len(banned)}",
            "majorDimension": "COLUMNS",
            "values": [banned]
        })
    params = {
        "valueInputOption": "RAW",
    }
    body = {
        "data": data
    }
    print(sh.values_batch_update(params, body))
    if ban:
        sh.values_batch_clear(body={"ranges": [f"Balances!A{len(ids)+1}:B{len(ids)+1}",
                                               f"bts!A{len(ids)+1}:A{len(ids)+1}"]})
    elif unban:
        sh.values_batch_clear(body={"ranges": [f"bts!B{len(banned) + 1}:B{len(banned) + 1}"]})



global cache
fetchCache()


@bot.command(name='award', help='admins can award cool dollars at their leisure.',
             usage='(name) (amount)')
async def award(ctx, *args):
    if not isAdmin(ctx.author):
        return
    if len(args) < 2:
        await ctx.send(f"$award expects a recipient and an amount")
        return
    print(cache)
    name = ' '.join(args[:-1])
    user = await toUser(ctx, name)
    if user is None:
        name = sanitize(name)
        await ctx.send(f"{name} is not a valid awardee")
        return
    amount = toValidDecimal(args[-1])
    if amount is None:
        amount = sanitize(args[-1])
        await ctx.send(f"{amount} is not a valid amount of Cool Dollars")
        return
    bal = await getBalance(user)
    if bal is None:
        newUser(user)
        bal = 25
    new_bal = bal + amount
    await setBalance(user, new_bal)
    await ctx.send(f"Awarded {amount:.2f} Cool Dollars to {await getName(user)}")
    pushCache()


@bot.command(name='setup', help='set up your cool dollar account',
             usage='[name]')
async def setup(ctx, *args):
    if ctx.author.id in cache["ids"]:
        name = await getName(ctx.author)
        await ctx.send(f"You're already a part of the economy, {name}.")
        return
    newUser(ctx.author)
    if len(args) != 0:
        await lock(ctx.author)
        name = ' '.join(args)
        cache["names"][userIndex(ctx.author)] = name
        await unlock(ctx.author)
    else:
        name = await getName(ctx.author)
    await ctx.send(f"Welcome to the economy, {name}! Your balance is 25.00 Cool Dollars.")
    pushCache()


@bot.command(name='sync', hidden=True)
async def sync(ctx, *args):
    fetchCache()
    await ctx.send("The bot is in sync with the spreadsheet.")

@bot.command(name='balance', help='check your or others\' cool dollar balances',
             usage='[name]')
async def balance(ctx, *, args=None):
    if args is not None:
        user = await toUser(ctx, args)
        if user is None:
            name = sanitize(args)
            await ctx.send(f"{name} is not a valid money haver")
            return
    else:
        user = ctx.author

    bal = await getBalance(user)
    await ctx.send(f"{await getName(user)} has {bal:.2f} Cool Dollars")


@bot.command(name='edit', hidden=True)
async def edit(ctx, *args):
    if isAdmin(ctx.author):
        edited = await toUser(ctx, args[0])
        if edited is not None:
            await setBalance(edited, Decimal(args[1]))
            pushCache()


@bot.command(name='test', hidden=True)
async def test(ctx, *args):
    print(sh.values_batch_get(["Balances!A:B", "bts!A:A", "bts!B:B"], {"majorDimension": "COLUMNS"}))


@bot.command(name='pay', help='pay someone cool dollars',
             usage='(name) (amount)')
async def pay(ctx, *args):
    if len(args) < 2:
        await ctx.send(f"$pay expects a recipient and an amount")
        return
    sender = str(ctx.author.id)
    name = ' '.join(args[:-1])
    rec_user = await toUser(ctx, name)
    if rec_user is None:
        name = sanitize(name)
        await ctx.send(f"{name} is not a valid recipient")
        return

    amount = toValidDecimal(args[-1])

    if amount is None:
        amount = sanitize(args[-1])
        await ctx.send(f"{amount} is not a valid amount of Cool Dollars")
        return
    if rec_user.id == ctx.author.id:
        await ctx.send(f"Cool. You sent yourself {amount:.2f} Cool Dollars.\nCongratulations. You have the same amount of money.")
        return
    send_balance = await getBalance(ctx.author)
    rec_balance = await getBalance(rec_user)

    if amount <= 0:
        await ctx.send(f"{amount:.2f} is not positive")
        return

    if amount > send_balance:
        await ctx.send(f"{amount:.2f} is more than your current balance, {send_balance:.2f}")
        return
    await setBalance(ctx.author, send_balance - amount)
    await setBalance(rec_user, rec_balance + amount)
    await ctx.send(f"{amount:.2f} was sent to {await getName(rec_user)}")
    pushCache()


@bot.command(name='name', help='change or set your name in the spreadsheet',
             usage='to see your current name\n'
                   '$name [new_name] to change names')
async def name(ctx, *, name=None):
    if name is None:
        name = await getName(ctx.author)
        await ctx.send(f"Your name is currently {name}.\n"
                       f"Use \"$name Your Name Here\" to change it")
        return
    name = sanitize(name)
    await lock(ctx.author)
    cache["names"][userIndex(ctx.author)] = name
    await ctx.send(f"Your name was was set to {name}")
    await unlock(ctx.author)
    pushCache()


@bot.command(name='ban', help='admins use to ban a user from the economy (and erase balance)',
             usage='(user) to ban user')
async def ban(ctx, *, name=""):
    if not isAdmin(ctx.author):
        return
    ban_user = await toUser(ctx, name)
    if ban_user is None:
        name = sanitize(name)
        await ctx.send(f"{name} is not a valid user to ban")
        return
    if ban_user.id in cache["banned"]:
        await ctx.send(f"{name} is already banned.")
        return
    await lock()
    cache["banned"].append(ban_user.id)
    if ban_user.id in cache["ids"]:
        idx = userIndex(ban_user)
        del cache["ids"][idx]
        del cache["balances"][idx]
        del cache["names"][idx]
    await unlock()
    await ctx.send(f"{name} was banned.")
    pushCache(ban=True)


@bot.command(name='unban', help='admins use to pardon a user from the economy (does not restore balance)',
             usage='(user) to unban user')
async def unban(ctx, *, name=""):
    if not isAdmin(ctx.author):
        return
    ban_user = await toUser(ctx, name)
    if ban_user is None:
        name = sanitize(name)
        await ctx.send(f"{name} is not a valid user.")
        return
    if ban_user.id not in cache["banned"]:
        await ctx.send(f"{name} is not a banned.")
        return
    cache["banned"].remove(ban_user.id)
    await ctx.send(f"{name} was unbanned. use $setup to rejoin the economy.")
    pushCache(unban=True)


async def lock(user=None):
    if user is None:
        for l in cache["user_locks"].values():
            await l.acquire()
        return
    out = cache["user_locks"].get(user.id)
    if out is None:
        newUser(user)
        out = cache["user_locks"].get(user.id)
    await out.acquire()


async def unlock(user=None):
    if user is None:
        for l in cache["user_locks"].values():
            l.release()
        return
    cache["user_locks"][user.id].release()


async def getName(user):
    await lock(user)
    out = cache["names"][userIndex(user)]
    await unlock(user)
    return out


async def setBalance(user, new_balance):
    await lock(user)
    idx = userIndex(user)
    cache["balances"][idx] = new_balance
    await unlock(user)


async def getBalance(user):
    await lock(user)
    idx = userIndex(user)
    out = cache["balances"][idx]
    await unlock(user)
    return out


def userIndex(user):
    try:
        idx = cache["ids"].index(user.id)
    except ValueError:
        newUser(user)
        idx = cache["ids"].index(user.id)
    return idx


class UserBannedError(commands.CommandError):
    pass


def newUser(user):
    if user.id in cache["banned"]:
        raise UserBannedError
    name = str(user)
    cache["ids"].append(user.id)
    cache["names"].append(str(user))
    cache["balances"].append(Decimal("25.00"))
    cache["user_locks"][user.id] = asyncio.Lock()


def isAdmin(user):
    return 693144828590162030 in [role.id for role in user.roles]


async def toUser(ctx, name):
    converter = commands.UserConverter()
    try:
        return await converter.convert(ctx, name)
    except commands.UserNotFound:
        try:
            return await bot.fetch_user(cache["ids"][cache["names"].index(name)])
        except ValueError:
            return None


def toValidDecimal(val):
    try:
        amount = Decimal(val)
        if amount.is_nan() or amount.is_infinite() or amount.is_subnormal():
            raise InvalidOperation
        amount = Decimal(amount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
        return amount
    except InvalidOperation:
        return None

def sanitize(input):
    return re.sub(r'<?(@|@!|#|@&|(a?:[a-zA-Z0-9_]+:))([0-9]+)>', sanitize_instance, input)

def sanitize_instance(mention):
    if mention.group(1)[0] == "@":
        return "@disallowed"
    elif mention.group(1) == "#":
        return "#disallowed"
    else:
        return ":disallowed:"

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, UserBannedError):
        await ctx.send("That user is banned. They cannot participate in the economy unless an admin uses $unban on them.")
        return
    elif isinstance(error, commands.CommandNotFound):
        content = sanitize(ctx.message.content)
        await ctx.send(f"{content} is not a valid command.")
        return
    elif isinstance(error, commands.ArgumentParsingError):
        await ctx.send("Nice try, Sherlock SQL Injection.")
        return
    await (await bot.fetch_channel(900027403919839282)).send(str(error))
    raise error




bot.run(TOKEN)
