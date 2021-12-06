from constants import BANNED_WORDS, PREFIXES, THOUSAND_YEARS_IN_SECS, TIME_DICT
from discord.ext import commands
import re
import grapheme
from cache import Cache
from obfuscate import obfuscate


class KnucTatsCog(commands.Cog):

    def __init__(self, bot, cache):
        self.bot = bot
        self.cache: Cache = cache

    @staticmethod
    def looks_like(amount: int):
        out = "\nThis is what that looks like:\n>>> "
        out += "HAND SETS\n" * amount
        return out

    def time_string(self, seconds: int):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        years, days = divmod(days, 365)
        weeks, days = divmod(days, 7)
        segments = []
        if years > 0:
            segments.append(f"{years} year" + ("s" if years > 1 else ""))
        if weeks > 0:
            segments.append(f"{weeks} week" + ("s" if weeks > 1 else ""))
        if days > 0:
            segments.append(f"{days} day" + ("s" if days > 1 else ""))
        if hours > 0:
            segments.append(f"{hours} hour" + ("s" if hours > 1 else ""))
        if minutes > 0:
            segments.append(f"{minutes} minute" + ("s" if minutes > 1 else ""))
        if seconds > 0 or len(segments) == 0:
            segments.append(f"{seconds} second" + ("s" if seconds > 1 else ""))

        out = ""
        for i in segments[:-1]:
            out += i + ", "
        if len(segments) > 1:
            out += "and "
        out += segments[-1]
        return out

    def to_seconds(self, parse: str):
        if parse == "":
            return -1
        try:
            out = float(parse)
        except ValueError:
            cleaned = re.sub(r'\s|,|and|for|\.', '', parse).lower()
            out = 0
            for m in re.finditer(r"([-+]?\d*\.?\d*)(y|w|d|h|m[^o]?|s)",
                                 cleaned):
                if m.group(1) != "" and m.group(1) != ".":
                    out += float(m.group(1)) * TIME_DICT[m.group(2)[0]]
        out = int(out)
        if out <= 0 or out >= THOUSAND_YEARS_IN_SECS:
            return None
        return out

    def format_knuc_tats(self, message, string=None):
        if message.author.bot or message.guild is None:
            return None
        if string is None:
            string = message.content
        guild_id = message.guild.id
        if len(string) < 1:
            # TODO: sometimes triggers on bot message, which should be caught above. figure out and fix.
            print(f"empty message with id {message.id}")
            return None
        if string[0] in PREFIXES:
            return None
        if self.cache.time_left(message.guild.id, message.guild.id) is not None or \
                self.cache.time_left(message.guild.id, message.channel.id) is not None:
            return
        wws = re.sub(r'\s', '', string).upper()
        obf_wws = obfuscate(wws)
        for word in BANNED_WORDS:
            if word in obf_wws:
                return None
        length = grapheme.length(wws)
        if length > 0 and length % 8 == 0 and length // 8 <= self.cache.get_server_max_hands(guild_id):
            tat = ""
            for i in range(0, length, 8):
                tat += f"{grapheme.slice(wws, i, i + 4)} {grapheme.slice(wws, i + 4, i + 8)}\n"
            tat = tat[:-1]

            self.cache.push_recent(message, tat)
            return tat
        return None
