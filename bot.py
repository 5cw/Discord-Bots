
import time

import gspread

startTime = time.time()

import discord
from discord.ext import commands
from dotenv import load_dotenv

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
        amount = float(args[-1])
    except ValueError:
        await ctx.send(f"{args[1]} is not a valid amount of Cool Dollars")
        return
    bal = getBalance(user.id)
    if bal is None:
        await newUser(user.id)
        bal = 25
    await setBalance(user.id, bal + amount)
    await ctx.send(f"Awarded {args[-1]} Cool Dollars to {await getName(user.id)}")

@bot.command(name='setup', help='set up your cool dollar account',
             usage='[name]')
async def setup(ctx, *args):
    await newUser(ctx.author.id)
    if len(args) == 0:
        return
    name = ' '.join(args)
    sh.worksheet("Balances").update_cell(await idIndex(ctx.author.id), 1, name)


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

    bal = getBalance(user.id)
    if bal is None:
        await newUser(user.id)
        bal = 25.0
    await ctx.send(f"{await getName(user.id)} has {bal:.2f} Cool Dollars")


@bot.command(name='edit', hidden=True)
async def edit(ctx, *args):
    if ctx.author.id == 999999999999999999:
        await setBalance(args[0], float(args[1]))


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
    amount = None
    try:
        amount = float(args[-1])
    except ValueError:
        await ctx.send(f"{args[-1]} is not a valid amount of Cool Dollars")
        return

    receiver = str(rec_user.id)

    print(receiver)
    send_balance = getBalance(sender)
    if send_balance is None:
        await newUser(sender)
        send_balance = 25.0
    rec_balance = getBalance(receiver)
    if rec_balance is None:
        await newUser(receiver)
        rec_balance = 25.0
    if amount is None:
        await ctx.send(f"That is not valid amount of Cool Dollars")
        return
    amount = round(amount, 2)

    if amount <= 0:
        await ctx.send(f"{amount:.2f} is not positive")
        return

    if amount > send_balance:
        await ctx.send(f"{amount:.2f} is more than your current balance, {send_balance:.2f}")
        return
    await setBalance(sender, send_balance - amount)
    await setBalance(receiver, rec_balance + amount)
    await ctx.send(f"{amount:.2f} was sent to {await getName(rec_user.id)}")


@bot.command(name='name', help='change or set your name in the spreadsheet',
             usage='to see your current name\n'
                   '$name [new_name] to change names')
async def name(ctx, *args):
    if len(args) == 0:
        name = getName(ctx.author.id)
        await ctx.send(f"Your name is currently {name}.\n"
                       f"Use \"$name Your Name Here\" to change it")
        return
    name = ' '.join(args)
    sh.worksheet("Balances").update_cell(await idIndex(ctx.author.id), 1, name)
    await ctx.send(f"Your name was was set to {name}")


async def getName(id):
    return sh.worksheet("Balances").cell(await idIndex(id), 1).value


async def setBalance(id, new_balance):
    idx = await idIndex(id)
    sh.worksheet("Balances").update_cell(idx, 2, new_balance)


def getBalance(id):
    balances = getBalances()
    try:
        return float(balances.get(str(id)))
    except TypeError:
        return None


def getBalances():
    return dict(zip(sh.worksheet("bts").col_values(1), sh.worksheet("Balances").col_values(2)))


async def idIndex(id):
    ids = sh.worksheet("bts").col_values(1)
    idx = None
    try:
        idx = ids.index(str(id))
    except ValueError:
        await newUser(id)
        ids = sh.worksheet("bts").col_values(1)
        idx = ids.index(id)
    return idx + 1


async def newUser(id):
    name = str(await bot.fetch_user(id))
    sh.worksheet("bts").append_row([str(id)])
    data = sh.worksheet("Balances").append_row([name, 25.00])
    range = data['updates']['updatedRange'].split(":")[1]
    sh.worksheet("Balances").format(range, {"numberFormat": {
        "type": "NUMBER",
        "pattern": "0.00"
    }})


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
bot.run(TOKEN)
