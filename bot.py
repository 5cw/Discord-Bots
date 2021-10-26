
import time

import gspread

startTime = time.time()

import discord
from discord.ext import commands
from dotenv import load_dotenv
from decimal import *

import os.path

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='$', intents=intents, help_command=commands.DefaultHelpCommand(
    no_category = 'Commands'
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
sh = gc.open_by_key(SPREADSHEET_ID, )
getcontext().prec = 2

@bot.command(name='award', help='admins can award cool dollars at their leisure.',
             usage= '(name) (amount)')
async def award(ctx, *args):
    if not isAdmin(ctx.author):
        return
    if len(args) < 2:
        await ctx.send(f"$award expects a recipient and an amount")
        return
    name = ' '.join(args[:-1])
    user = await toUser(ctx, name)
    if user is None:
        await ctx.send(f"{name} is not a valid awardee")
        return
    amount = None
    try:
        amount = Decimal(args[-1])
    except decimal.InvalidOperation:
        await ctx.send(f"{args[1]} is not a valid amount of Cool Dollars")
        return
    bal = getBalance(user)
    if bal is None:
        newUser(user)
        bal = 25
    new_bal = bal + amount
    await setBalance(user, new_bal)
    await ctx.send(f"Awarded {amount:.2f} Cool Dollars to {await getName(user)}")

@bot.command(name='setup', help='set up your cool dollar account',
             usage='[name]')
async def setup(ctx, *args):
    await newUser(ctx.author)
    if len(args) == 0:
        return
    name = ' '.join(args)
    sh.worksheet("Balances").update_cell(userIndex(ctx.author), 1, name)


@bot.command(name='balance', help='check your cool dollar balance',
             usage='[name] (only admins may see others\' balances)')
async def balance(ctx, *args):
    user = None
    if len(args) != 0 and isAdmin(ctx.author):
        user = await toUser(ctx, ' '.join(args))
        if user is None:
            await ctx.send(f"{args[0]} is not a valid money haver")
            return
    else:
        user = ctx.author

    bal = getBalance(user)
    await ctx.send(f"{await getName(user)} has {bal:.2f} Cool Dollars")


@bot.command(name='edit', hidden=True)
async def edit(ctx, *args):
    if isAdmin(ctx.author):
        edited = await toUser(ctx, args[0])
        if edited is not None:
            await setBalance(edited, Decimal(args[1]))


@bot.command(name='test', hidden=True)
async def test(ctx, *args):
    pass


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
        await ctx.send(f"{name} is not a valid recipient")
        return
    try:
        amount = Decimal(args[-1])
    except decimal.InvalidOperation:
        await ctx.send(f"{args[-1]} is not a valid amount of Cool Dollars")
        return


    send_balance = getBalance(ctx.author)
    rec_balance = getBalance(ctx.author)
    amount = round(amount, 2)

    if amount <= 0:
        await ctx.send(f"{amount:.2f} is not positive")
        return

    if amount > send_balance:
        await ctx.send(f"{amount:.2f} is more than your current balance, {send_balance:.2f}")
        return
    await setBalance(ctx.author, send_balance - amount)
    await setBalance(rec_user, rec_balance + amount)
    await ctx.send(f"{amount:.2f} was sent to {await getName(rec_user)}")


@bot.command(name='name', help='change or set your name in the spreadsheet',
             usage='to see your current name\n'
                   '$name [new_name] to change names')
async def name(ctx, *args):
    if len(args) == 0:
        name = getName(ctx.author)
        await ctx.send(f"Your name is currently {name}.\n"
                       f"Use \"$name Your Name Here\" to change it")
        return
    name = ' '.join(args)
    sh.worksheet("Balances").update_cell(userIndex(ctx.author), 1, name)
    await ctx.send(f"Your name was was set to {name}")


async def getName(user):
    return sh.worksheet("Balances").cell(userIndex(user), 1).value


async def setBalance(user, new_balance):
    idx = userIndex(user)
    sh.worksheet("Balances").update_cell(idx, 2, str(new_balance))


def getBalance(user):
    balances = getBalances()
    try:
        return Decimal(balances.get(str(user.id)))
    except TypeError:
        newUser(user)
        return Decimal("25.00")


def getBalances():
    return dict(zip(sh.worksheet("bts").col_values(1), sh.worksheet("Balances").col_values(2)))


def userIndex(user):
    ids = sh.worksheet("bts").col_values(1)
    idx = None
    try:
        idx = ids.index(str(user.id))
    except ValueError:
        newUser(user)
        ids = sh.worksheet("bts").col_values(1)
        idx = ids.index(str(user.id))
    return idx + 1


def newUser(user):
    name = str(user)
    sh.worksheet("bts").append_row([str(user.id)])
    data = sh.worksheet("Balances").append_row([name, "25.00"])



def isAdmin(user):
    return 693144828590162030 in [role.id for role in user.roles]

async def toUser(ctx, name):
    converter = commands.UserConverter()
    try:
        return await converter.convert(ctx, name)
    except commands.UserNotFound:
        names = sh.worksheet("Balances").col_values(1)
        ids = sh.worksheet("bts").col_values(1)
        try:
            return await bot.fetch_user(int(ids[names.index(name)]))
        except ValueError:
            return None

@bot.event
async def on_command_error(ctx, error):
    await (await bot.fetch_channel(900027403919839282)).send(str(error))
bot.run(TOKEN)
