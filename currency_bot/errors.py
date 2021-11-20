from discord.ext import commands


class UserBannedError(commands.CommandError):
    pass


class DecimalizationError(commands.CommandError):
    def __init__(self, amount):
        super()
        self.amount = amount


class UnknownAPIError(commands.CommandError):
    pass