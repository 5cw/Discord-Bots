from knuc_tats_cog import KnucTatsCog
from discord.ext import commands



class MessageHandler(KnucTatsCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        tats = self.format_knuc_tats(message)
        if tats:
            await message.channel.send(tats)
