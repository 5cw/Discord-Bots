from discord.ext import commands
from currency_cog import CurrencyCog
from constants import PLURAL_CURRENCY_NAME


class Admin(CurrencyCog):

    @commands.has_permissions(manage_guild=True)
    @commands.command(name='edit', hidden=True)
    async def edit(self, ctx, *args):
        edited = await self.to_user(ctx, ' '.join(args[:-1]))
        amount = self.to_decimal(args[-1])
        await self.cache.set_balance(edited, amount)
        await self.cache.push_cache()

    @commands.has_permissions(manage_guild=True)
    @commands.command(name='award', help=f'award {PLURAL_CURRENCY_NAME.lower()} at your leisure.',
                      usage='(name) (amount)')
    async def award(self, ctx, *args):
        if len(args) < 2:
            await ctx.send(f"$award expects a recipient and an amount")
            return
        name = ' '.join(args[:-1])
        user = await self.to_user(ctx, name)
        amount = self.to_decimal(args[-1])
        bal = await self.cache.get_balance(user)
        if bal is None:
            self.cache.new_user(user)
            bal = 25
        new_bal = bal + amount
        if abs(new_bal) > self.cache.MAX_BALANCE:
            new_bal = self.cache.MAX_BALANCE.copy_sign(new_bal)
            amount = new_bal - bal
        await self.cache.set_balance(user, new_bal)
        await self.cache.push_cache()
        await ctx.send(f"Awarded {amount:.2f} {plural_currency(amount)} to {await self.cache.get_name(user)}")

    @commands.has_permissions(manage_guild=True)
    @commands.command(name='ban', help='use to ban a user from the economy (and erase balance)',
                      usage='(user) to ban user')
    async def ban(self, ctx, *, name=""):
        ban_user = await self.to_user(ctx, name)
        if ban_user.id in self.cache.banned:
            await ctx.send(f"{name} is already banned.")
            return
        await self.cache.ban(ban_user)
        await ctx.send(f"{str(ban_user)} was banned.")
        await self.cache.push_cache(ban=True)

    @commands.has_permissions(manage_guild=True)
    @commands.command(name='unban', help='use to pardon a user from the economy (does not restore balance)',
                      usage='(user) to unban user')
    async def unban(self, ctx, *, name=""):
        ban_user = await self.to_user(ctx, name)
        if ban_user.id not in self.cache.banned:
            await ctx.send(f"{str(ban_user)} is not banned.")
            return
        await self.cache.unban(ban_user)
        await ctx.send(f"{str(ban_user)} was unbanned. use $setup to rejoin the economy.")
        await self.cache.push_cache(unban=True)
