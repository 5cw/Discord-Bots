import discord
from discord.ext import commands


from knuc_tats_cog import KnucTatsCog

class FlagError(Exception):

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(*args)

    def __str__(self) -> str:
        return self.__repr__()


    def __repr__(self) -> str:
        return self.message

    message: str


class BadWordError(Exception):

    def __init__(self, contextual_string: str, *args: object) -> None:
        self.contextual_string = contextual_string
        super().__init__(*args)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.contextual_string} tats were dropped for containing offensive words. Aborting."

    contextual_string: str

class ErrorHandler(KnucTatsCog):

    rate_limited = False

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"That is not a valid command.")
            return
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send("Nice try, Sherlock SQL Injection.")
            return
        elif isinstance(error, BadWordError) or isinstance(error, FlagError):
            await ctx.send(error)
            return
        elif isinstance(error, discord.HTTPException):
            print(error.response)
        else:
            await (await self.bot.fetch_channel(944217254290137138)).send(str(error))
        raise error

    @commands.Cog.listener()
    async def on_ready(self):
        print("knuc tats bot ready!")