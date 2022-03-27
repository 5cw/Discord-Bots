from currency_cog import CurrencyCog, plural_currency
from errors import UserBannedError, DecimalizationError
from discord.ext import commands

class ErrorHandler(CurrencyCog):

    @commands.check
    async def is_rate_limited(self, ctx):
        if self.cache.rate_limited:
            await ctx.send("Too many Google Sheets API calls. Slow down.")
        return not self.cache.rate_limited

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, UserBannedError):
            await ctx.send(
                "That user is banned. They cannot participate in the economy unless an admin uses $unban on them.")
            return
        elif isinstance(error, commands.CommandNotFound):
            content = self.sanitize(ctx, ctx.message.content)
            await ctx.send(f"{content} is not a valid command.")
            return
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send("Nice try, Sherlock SQL Injection.")
            return
        elif isinstance(error, DecimalizationError):
            amount = self.sanitize(ctx, error.amount)
            await ctx.send(f"{amount} is not a valid amount of {plural_currency(amount)}.")
            return
        elif isinstance(error, commands.UserNotFound):
            name = self.sanitize(ctx, error.argument)
            await ctx.send(f"{name} is not a valid user.")
        else:
            await (await self.bot.fetch_channel(944217254290137138)).send(str(error))
        raise error

    @commands.Cog.listener()
    async def on_ready(self):
        print("currency bot ready!")