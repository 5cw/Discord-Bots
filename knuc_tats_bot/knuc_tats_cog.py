import dataclasses

from constants import BANNED_WORDS, PREFIXES, THOUSAND_YEARS_IN_SECS, TIME_DICT, SPLIT
from discord.ext import commands
import re
import grapheme
from cache import Cache
from obfuscate import obfuscate


def to_seconds(parse: str):
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


def time_string(seconds: int):
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

@dataclasses.dataclass
class KnucTats:
    text: str
    is_bad_word: bool

class KnucTatsCog(commands.Cog):

    def __init__(self, bot, cache):
        self.bot = bot
        self.cache: Cache = cache

    @staticmethod
    def looks_like(amount: int):
        out = "\nThis is what that looks like:\n>>> "
        out += "HAND SETS\n" * amount
        return out

    def batch_check_and_format(self, message, string=None):
        if string is None:
            string = message.content
        return [tat for tat in
         [self.check_and_format(message, potential)
          for potential in string.split(SPLIT)]
         if tat is not None]


    def check_and_format(self, message, string=None):
        if message.author.bot or message.guild is None:
            return None
        strict = string is None
        if strict:
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
        split_wws = re.split(r'\s', string)
        wws = ''.join(split_wws).upper()
        obf_wws = obfuscate(wws)
        bad_word_found = False
        for word in BANNED_WORDS:
            if word in obf_wws:
                bad_word_found = True
                break
        max = self.cache.get_server_max_hands(message.guild.id)
        length = grapheme.length(wws)
        valid = length > 0 and length % 8 == 0
        if strict and valid:

            tally = 0
            for word in split_wws:
                tally += grapheme.length(word)
                if tally == 8:
                    tally = 0
                    max -= 1
                elif tally > 8:
                    valid = False
                    break
            if max < 0 or tally != 0:
                return None
        
        if valid:
            tat = ""
            for i in range(0, grapheme.length(wws), 8):
                tat += f"{grapheme.slice(wws, i, i + 4)} {grapheme.slice(wws, i + 4, i + 8)}\n"
            tat = tat[:-1]
            if not bad_word_found:
                self.cache.push_recent(message, tat)
            return KnucTats(tat, bad_word_found)
        return None

    