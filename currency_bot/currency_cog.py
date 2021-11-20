from discord.ext import commands
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from errors import DecimalizationError, UserBannedError
from constants import CURRENCY_NAME, PLURAL_CURRENCY_NAME
import re

class CurrencyCog(commands.Cog):
    converter = commands.UserConverter()

    def __init__(self, bot, cache):
        self.bot = bot
        self.cache = cache

    async def to_user(self, ctx, name):
        try:
            return self.bot.get_user(self.cache.ids[self.cache.names.index(name)])
        except ValueError:
            return await CurrencyCog.converter.convert(ctx, name)

    def to_decimal(self, val):
        try:
            amount = Decimal(val)
            print(amount)
            if amount.is_nan() or amount.is_infinite():
                raise DecimalizationError(val)
            elif abs(amount) > (2 * self.cache.MAX_BALANCE):
                amount = (2 * self.cache.MAX_BALANCE).copy_sign(amount)
            else:
                amount = Decimal(amount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
            return amount
        except InvalidOperation:
            raise DecimalizationError(val)

    def sanitize(self, ctx, input):
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
                channel = self.bot.get_channel(id) or nf
                return f"#{channel}"
            else:
                return m.group(2)

        return re.sub(r'<?(@|@!|#|@&|a?(:[a-zA-Z0-9_]+:))([0-9]+)>', sanitize_helper, input)

    def plural_currency(self, amt):
        if amt != 1:
            return PLURAL_CURRENCY_NAME
        else:
            return CURRENCY_NAME