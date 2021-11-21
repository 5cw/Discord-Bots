from constants import TIME_DICT, THOUSAND_YEARS_IN_SECS, MAX_HAND_SETS
from discord.ext import commands
import discord
import re
from time import time


class KnucTatsCog(commands.Cog):
    server_max_hands = {}
    server_recent_tat = {}
    server_disabled = {}

    def __init__(self, bot):
        self.bot = bot

    @classmethod
    def looks_like(cls, amount: int):
        out = "\nThis is what that looks like:\n>>> "
        out += "HAND SETS\n" * amount
        return out

    @classmethod
    def time_left(cls, guild_id: int, channel_id: int):
        if guild_id not in cls.server_disabled.keys():
            cls.server_disabled[guild_id] = {}
        if channel_id not in cls.server_disabled[guild_id].keys():
            return None
        curr = time()
        until = cls.server_disabled[guild_id][channel_id]
        if until > 0:
            left = until - curr
            print(left)
            if left <= 0:
                del cls.server_disabled[guild_id][channel_id]
                return None
            return left
        else:
            return -1

    @classmethod
    def time_string(cls, seconds: int):
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

    @classmethod
    def to_seconds(cls, parse: str):
        if parse == "":
            return -1
        try:
            out = float(parse)
        except ValueError:
            cleaned = re.sub(r'\s|,|and|for|\.', '', parse).lower()
            print(cleaned)
            out = 0
            for m in re.finditer(r"([-+]?\d*\.?\d*)(y|w|d|h|m^(?:onth)|s)",
                                 cleaned):
                if m.group(1) != "" and m.group(1) != ".":
                    out += float(m.group(1)) * TIME_DICT[m.group(2)[0]]
        out = int(out)
        if out <= 0 or out >= THOUSAND_YEARS_IN_SECS:
            return None
        return out

    @classmethod
    def set_recent(cls, message: discord.Message, tats: str):
        if message.guild.id not in cls.server_recent_tat.keys():
            cls.server_recent_tat[message.guild.id] = {}
        cls.server_recent_tat[message.guild.id][message.channel.id] = tats

    @classmethod
    def get_recent(cls, ctx):
        if ctx.guild.id not in cls.server_recent_tat.keys():
            cls.server_recent_tat[ctx.guild.id] = {}
        return cls.server_recent_tat[ctx.guild.id].get(ctx.channel.id)

    @classmethod
    def get_server_max_hands(cls, guild_id):
        out = cls.server_max_hands.get(guild_id)
        if out is None:
            out = cls.server_max_hands[guild_id] = MAX_HAND_SETS
        return out

    @classmethod
    def set_server_max_hands(cls, guild_id, amt):
        cls.server_max_hands[guild_id] = amt

    @classmethod
    def enable(cls, guild_id, channel_id):
        if channel_id is None:
            cls.server_disabled[guild_id].clear()
        else:
            del cls.server_disabled[guild_id][channel_id]

    @classmethod
    def disable(cls, guild_id, channel_id, length):
        cls.server_disabled[guild_id][channel_id] = length
