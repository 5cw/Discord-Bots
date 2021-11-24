import json

import github3

from constants import TIME_DICT, THOUSAND_YEARS_IN_SECS, MAX_HAND_SETS, BANNED_WORDS, PREFIXES, \
    GITHUB_GISTS_TOKEN, GITHUB_USERNAME, GITHUB_PASSWORD
from discord.ext import commands
import discord
import re
from time import time
import grapheme


class KnucTatsCog(commands.Cog):
    server_max_hands = {}
    server_recent_tat = {}
    server_disabled = {}
    gist = None
    if GITHUB_GISTS_TOKEN:
        gh = github3.login(token=GITHUB_GISTS_TOKEN)
    else:
        gh = github3.login(username=GITHUB_USERNAME, password=GITHUB_PASSWORD)
    for gist in gh.gists():
        if 'tweet-bin.json' in gist.files.keys():
            gist = gist
            break
    else:
        raise FileNotFoundError
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
        cls.save()

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
        cls.save()

    @classmethod
    def enable(cls, guild_id, channel_id):
        if channel_id is None:
            cls.server_disabled[guild_id].clear()
        else:
            del cls.server_disabled[guild_id][channel_id]
        cls.save()

    @classmethod
    def disable(cls, guild_id, channel_id, length):
        cls.server_disabled[guild_id][channel_id] = length
        cls.save()

    @classmethod
    def fetch(cls):
        properties = cls.gist.files.get('properties.json')
        if properties:
            try:
                data = json.loads(properties.content())
                cls.server_max_hands = data.get('server_max_hands') or {}
                cls.server_recent_tat = data.get('server_recent_tat') or {}
                cls.server_disabled = data.get('server_disabled') or {}
            except json.JSONDecodeError:
                print("malformed properties.json")
        return cls.gist.files['tweet-bin.json'].content()

    @classmethod
    def save(cls, tweets=None):
        properties = json.dumps({
            'server_max_hands': cls.server_max_hands,
            'server_recent_tat': cls.server_recent_tat,
            'server_disabled': cls.server_disabled
        }, indent=2)
        files = {'properties.json': {'content': properties}}
        if tweets:
            files['tweet-bin.json'] = {'content': tweets}
        cls.gist.edit(files=files)

    def format_knuc_tats(self, message, string=None):
        if message.author.bot or message.guild is None:
            return
        if string is None:
            string = message.content
        guild_id = message.guild.id
        if len(string) < 1:
            print(f"empty message with id {message.id}")
            return
        if string[0] in PREFIXES:
            return
        if self.time_left(message.guild.id, message.guild.id) is not None or \
                self.time_left(message.guild.id, message.channel.id) is not None:
            return
        wws = re.sub(r'\s', '', string)
        for word in BANNED_WORDS:
            if word in wws:
                return
        length = grapheme.length(wws)
        if length > 0 and length % 8 == 0 and length // 8 <= self.get_server_max_hands(guild_id):
            tat = ""
            for i in range(0, length, 8):
                tat += f"{grapheme.slice(wws, i, i + 4)} {grapheme.slice(wws, i + 4, i + 8)}\n".upper()
            tat = tat[:-1]
            self.set_recent(message, tat)
            return tat
        return None