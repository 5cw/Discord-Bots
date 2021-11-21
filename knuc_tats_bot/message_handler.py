from knuc_tats_cog import KnucTatsCog
from discord.ext import commands
from constants import PREFIXES, BANNED_WORDS
import grapheme
import re


class MessageHandler(KnucTatsCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return
        guild_id = message.guild.id
        if len(message.content) < 1:
            print(f"empty message with id {message.id}")
            return
        if message.content[0] in PREFIXES:
            return
        if self.time_left(message.guild.id, message.guild.id) is not None or \
                self.time_left(message.guild.id, message.channel.id) is not None:
            return
        wws = re.sub(r'\s', '', message.content)
        for word in BANNED_WORDS:
            if word in wws:
                return
        length = grapheme.length(wws)
        if length > 0 and length % 8 == 0 and length // 8 <= self.get_server_max_hands(guild_id):
            tat = ""
            for i in range(0, length, 8):
                tat += f"{grapheme.slice(wws, i, i + 4)} {grapheme.slice(wws, i + 4, i + 8)}\n".upper()
            await message.channel.send(tat)
            self.set_recent(message, tat)