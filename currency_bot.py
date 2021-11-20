from cache import *

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

cd_bot = commands.Bot(command_prefix='$', intents=intents, help_command=commands.DefaultHelpCommand(
    no_category='Commands'
))
dotenv.load_dotenv()
C_TOKEN = os.environ['CD_TOKEN']
converter = commands.UserConverter()

CURRENCY_NAME = os.environ['CURRENCY_NAME']

global cache


@cd_bot.command(name='award', help=f'admins can award {CURRENCY_NAME.lower()} at their leisure.',
             usage='(name) (amount)')
async def award(ctx, *args):
    if not is_admin(ctx.author):
        return
    if len(args) < 2:
        await ctx.send(f"$award expects a recipient and an amount")
        return
    print(cache)
    name = ' '.join(args[:-1])
    user = await to_user(ctx, name)
    amount = to_decimal(args[-1])
    bal = await cache.get_balance(user)
    if bal is None:
        cache.new_user(user)
        bal = 25
    new_bal = bal + amount
    if abs(new_bal) > cache.MAX_BALANCE:
        new_bal = cache.MAX_BALANCE.copy_sign(new_bal)
        amount = new_bal - bal
    await cache.set_balance(user, new_bal)
    await cache.push_cache()
    await ctx.send(f"Awarded {amount:.2f} {CURRENCY_NAME} to {await cache.get_name(user)}")


@cd_bot.command(name='setup', help='set up your cool dollar account',
             usage='[name]')
async def setup(ctx, *, args=None):
    if ctx.author.id in cache.ids:
        name = await cache.get_name(ctx.author)
        await ctx.send(f"You're already a part of the economy, {name}.")
        return
    cache.new_user(ctx.author)
    if args is not None and len(args) != 0:
        name = args
        await cache.set_name(ctx.author, name)
    else:
        name = str(ctx.author)
    await ctx.send(f"Welcome to the economy, {name}! Your balance is 25.00 {CURRENCY_NAME}.")
    await cache.push_cache()


@cd_bot.command(name='sync', hidden=True)
async def sync(ctx, *args):
    cache.fetch_cache()
    await ctx.send("The bot is in sync with the spreadsheet.")


@cd_bot.command(name='balance', help='check your or others\' cool dollar balances',
             usage='[name]')
async def balance(ctx, *, args=None):
    if args is not None and len(args) != 0:
        user = await to_user(ctx, args)
    else:
        user = ctx.author

    bal = await cache.get_balance(user)
    await ctx.send(f"{await cache.get_name(user)} has {bal:.2f} {CURRENCY_NAME}")


@cd_bot.command(name='edit', hidden=True)
async def edit(ctx, *args):
    if is_admin(ctx.author):
        edited = await to_user(ctx, ' '.join(args[:-1]))
        amount = to_decimal(args[-1])
        await cache.set_balance(edited, amount)
        await cache.push_cache()


@cd_bot.command(name='test', hidden=True)
async def test(ctx, *args):
    print(cache.sh.values_batch_get(["Balances!A:B", "bts!A:A", "bts!B:B"], {"major_dimension": "COLUMNS"}))


@cd_bot.command(name='pay', help=f'pay someone {CURRENCY_NAME.lower()}',
             usage='(name) (amount)')
async def pay(ctx, *args):
    if len(args) < 2:
        await ctx.send(f"$pay expects a recipient and an amount")
        return
    name = ' '.join(args[:-1])
    rec_user = await to_user(ctx, name)
    amount = to_decimal(args[-1])
    if rec_user.id == ctx.author.id:
        await ctx.send(
            f"Cool. You sent yourself {amount:.2f} {CURRENCY_NAME}.\nCongratulations. You have the same amount of money.")
        return
    send_balance = await cache.get_balance(ctx.author)
    rec_balance = await cache.get_balance(rec_user)

    if amount <= 0:
        await ctx.send(f"{amount:.2f} is not positive")
        return

    if amount > send_balance:
        await ctx.send(f"{amount:.2f} is more than your current balance, {send_balance:.2f}")
        return
    new_bal = rec_balance + amount
    if new_bal > cache.MAX_BALANCE:
        new_bal = cache.MAX_BALANCE
        amount = cache.MAX_BALANCE - rec_balance
    await cache.set_balance(ctx.author, send_balance - amount)
    await cache.set_balance(rec_user, new_bal)
    await ctx.send(f"{amount:.2f} was sent to {await cache.get_name(rec_user)}")
    await cache.push_cache()


@cd_bot.command(name='name', help='change or set your name in the spreadsheet',
             usage='to see your current name\n'
                   '$name [new_name] to change names')
async def name(ctx, *, name=None):
    if name is None or name == "":
        name = await cache.get_name(ctx.author)
        await ctx.send(f"Your name is currently {name}.\n"
                       f"Use \"$name Your Name Here\" to change it")
        return
    name = sanitize(ctx, name)
    await cache.set_name(ctx.author, name)
    await ctx.send(f"Your name was was set to {name}")
    await cache.push_cache()


@cd_bot.command(name='ban', help='admins use to ban a user from the economy (and erase balance)',
             usage='(user) to ban user')
async def ban(ctx, *, name=""):
    if not is_admin(ctx.author):
        return
    ban_user = await to_user(ctx, name)
    if ban_user.id in cache.banned:
        await ctx.send(f"{name} is already banned.")
        return
    await cache.ban(ban_user)
    await ctx.send(f"{str(ban_user)} was banned.")
    await cache.push_cache(ban=True)


@cd_bot.command(name='unban', help='admins use to pardon a user from the economy (does not restore balance)',
             usage='(user) to unban user')
async def unban(ctx, *, name=""):
    if not is_admin(ctx.author):
        return
    ban_user = await to_user(ctx, name)
    if ban_user.id not in cache.banned:
        await ctx.send(f"{str(ban_user)} is not banned.")
        return
    await cache.unban(ban_user)
    await ctx.send(f"{str(ban_user)} was unbanned. use $setup to rejoin the economy.")
    await cache.push_cache(unban=True)


def is_admin(user):
    return 693144828590162030 in [role.id for role in user.roles]


async def to_user(ctx, name):
    try:
        return cd_bot.get_user(cache.ids[cache.names.index(name)])
    except ValueError:
        return await converter.convert(ctx, name)


def to_decimal(val):
    try:
        amount = Decimal(val)
        print(amount)
        if amount.is_nan() or amount.is_infinite():
            raise DecimalizationError(val)
        elif abs(amount) > (2 * cache.MAX_BALANCE):
            amount = (2 * cache.MAX_BALANCE).copy_sign(amount)
        else:
            amount = Decimal(amount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
        return amount
    except InvalidOperation:
        raise DecimalizationError(val)


def sanitize(ctx, input):
    def sanitize_helper(m):
        nf = "not_found"
        id = int(m.group(3))
        if m.group(1)[0] == "@":
            if len(m.group(1)) > 1 and m.group(1)[1] == "&":
                role = ctx.guild.get_role(id) or nf
                return f"@{role}"
            else:
                user = ctx.guild.get_member(id)
                if user is None:
                    name = nf
                else:
                    name = user.display_name
                return f"@{name}"
        elif m.group(1) == "#":
            channel = cd_bot.get_channel(id) or nf
            return f"#{channel}"
        else:
            return m.group(2)

    return re.sub(r'<?(@|@!|#|@&|a?(:[a-zA-Z0-9_]+:))([0-9]+)>', sanitize_helper, input)


log_errors_in_channel = os.name != "nt"
if log_errors_in_channel:
    @cd_bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, UserBannedError):
            await ctx.send(
                "That user is banned. They cannot participate in the economy unless an admin uses $unban on them.")
            return
        elif isinstance(error, commands.CommandNotFound):
            content = sanitize(ctx, ctx.message.content)
            await ctx.send(f"{content} is not a valid command.")
            return
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send("Nice try, Sherlock SQL Injection.")
            return
        elif isinstance(error, DecimalizationError):
            amount = sanitize(ctx, error.amount)
            await ctx.send(f"{amount} is not a valid amount of {CURRENCY_NAME}.")
            return
        elif isinstance(error, commands.UserNotFound):
            name = sanitize(ctx, error.argument)
            await ctx.send(f"{name} is not a valid user.")
        else:
            await (await cd_bot.fetch_channel(900027403919839282)).send(str(error))
        raise error


@cd_bot.check
async def is_rate_limited(ctx):
    if cache.rate_limited:
        await ctx.send("Too many Google Sheets API calls. Slow down.")
    return not cache.rate_limited


@cd_bot.event
async def on_ready():
    global cache
    cache = Cache()
    await cache.fetch_cache()
    print(getcontext().prec)


cd_bot.run(CD_TOKEN)
