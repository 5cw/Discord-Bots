from discord.ext import commands
from currency_cog import CurrencyCog
from constants import PLURAL_CURRENCY_NAME


class General(CurrencyCog):

    @commands.command(name='setup', help=f'set up your {PLURAL_CURRENCY_NAME} account',
                      usage='[name]')
    async def setup(self, ctx, *, args=None):
        if ctx.author.id in self.cache.ids:
            name = await self.cache.get_name(ctx.author)
            await ctx.send(f"You're already a part of the economy, {name}.")
            return
        self.cache.new_user(ctx.author)
        if args is not None and len(args) != 0:
            name = args
            await self.cache.set_name(ctx.author, name)
        else:
            name = str(ctx.author)
        await ctx.send(f"Welcome to the economy, {name}! Your balance is 25.00 {PLURAL_CURRENCY_NAME}.")
        await self.cache.push_cache()

    @commands.has_permissions(manage_guild=True)
    @commands.command(name='sync', hidden=True)
    async def sync(self, ctx, *args):
        self.cache.fetch_cache()
        await ctx.send("The bot is in sync with the spreadsheet.")

    @commands.command(name='balance', help='check your or others\' cool dollar balances',
                      usage='[name]')
    async def balance(self, ctx, *, args=None):
        if args is not None and len(args) != 0:
            user = await self.to_user(ctx, args)
        else:
            user = ctx.author

        bal = await self.cache.get_balance(user)
        await ctx.send(f"{await self.cache.get_name(user)} has {bal:.2f} {self.plural_currency(bal)}")

    @commands.command(name='pay', help=f'pay someone {PLURAL_CURRENCY_NAME.lower()}',
                      usage='(name) (amount)')
    async def pay(self, ctx, *args):
        if len(args) < 2:
            await ctx.send(f"$pay expects a recipient and an amount")
            return
        name = ' '.join(args[:-1])
        rec_user = await self.to_user(ctx, name)
        amount = self.to_decimal(args[-1])
        if rec_user.id == ctx.author.id:
            await ctx.send(
                f"Cool. You sent yourself {amount:.2f} {self.plural_currency(amount)}.\nCongratulations. You have the same amount of money.")
            return
        send_balance = await self.cache.get_balance(ctx.author)
        rec_balance = await self.cache.get_balance(rec_user)

        if amount <= 0:
            await ctx.send(f"{amount:.2f} is not positive")
            return

        if amount > send_balance:
            await ctx.send(f"{amount:.2f} is more than your current balance, {send_balance:.2f}")
            return
        new_bal = rec_balance + amount
        if new_bal > self.cache.MAX_BALANCE:
            new_bal = self.cache.MAX_BALANCE
            amount = self.cache.MAX_BALANCE - rec_balance
        await self.cache.set_balance(ctx.author, send_balance - amount)
        await self.cache.set_balance(rec_user, new_bal)
        await ctx.send(f"{amount:.2f} was sent to {await self.cache.get_name(rec_user)}")
        await self.cache.push_cache()

    @commands.command(name='name', help='change or set your name in the spreadsheet',
                      usage='to see your current name\n'
                            '$name [new_name] to change names')
    async def name(self, ctx, *, name=None):
        if name is None or name == "":
            name = await self.cache.get_name(ctx.author)
            await ctx.send(f"Your name is currently {name}.\n"
                           f"Use \"$name Your Name Here\" to change it")
            return
        name = self.sanitize(ctx, name)
        await self.cache.set_name(ctx.author, name)
        await ctx.send(f"Your name was was set to {name}")
        await self.cache.push_cache()

    @commands.command(name='spreadsheet', help='sends the spreadsheet url',
                      usage='to see your current name\n'
                            '$name [new_name] to change names')
    async def spreadsheet(self, ctx, *, name=None):
        await ctx.send(self.cache.sh.url)
