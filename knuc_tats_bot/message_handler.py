from knuc_tats_cog import KnucTatsCog
from discord.ext import commands
from time import perf_counter


class MessageHandler(KnucTatsCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        before = perf_counter()
        tats = self.format_knuc_tats(message)

        print(before - perf_counter())
        if tats:
            await message.channel.send(tats)

