from knuc_tats_cog import KnucTatsCog
from discord.ext import commands

class MessageHandler(KnucTatsCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        tats = self.check_and_format(message)
        if tats and not tats.is_bad_word:
            await message.channel.send(tats.text)
