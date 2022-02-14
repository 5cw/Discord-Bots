import asyncio
import json
import discord
import grapheme

from constants import MAX_HAND_SETS, GIST, TWITTER_TIME_FORMAT, MESSAGE_LIMIT, HIST_MAX
from time import time
import datetime
import format


class Cache:
    
    def __init__(self):
        self.server_max_hands = None
        self.server_recent_tat = None
        self.server_disabled = None
        self.tweets = None
        self.latest = None
        self.bot_id = None
        properties = GIST.files.get('properties.json')
        if properties:
            try:
                data = json.loads(properties.content())
                self.server_max_hands = data.get('server_max_hands') or {}
                self.server_recent_tat = data.get('server_recent_tat') or {}
                self.server_disabled = data.get('server_disabled') or {}
            except json.JSONDecodeError:
                print("malformed properties.json")
        s = GIST.files['tweet-bin.json'].content()
        data = json.loads(s)
        self.tweets = data['tweets']
        self.latest = datetime.datetime.strptime(data['latest'], TWITTER_TIME_FORMAT)

    def time_left(self, guild_id: int, channel_id: int):
        guild_id = str(guild_id)
        channel_id = str(channel_id)
        if guild_id not in self.server_disabled.keys():
            self.server_disabled[guild_id] = {}
        if channel_id not in self.server_disabled[guild_id].keys():
            return None
        curr = time()
        until = self.server_disabled[guild_id][channel_id]
        if until > 0:
            left = until - curr
            print(left)
            if left <= 0:
                del self.server_disabled[guild_id][channel_id]
                return None
            return left
        else:
            return -1

    def push_recent(self, message: discord.Message, tats: str):
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        if guild_id not in self.server_recent_tat.keys():
            self.server_recent_tat[guild_id] = {}
        if channel_id not in self.server_recent_tat[guild_id].keys() \
                or type(self.server_recent_tat[guild_id][channel_id]) != list:
            self.server_recent_tat[guild_id][channel_id] = []
        self.server_recent_tat[guild_id][channel_id].insert(0, tats)
        if len(self.server_recent_tat[guild_id][channel_id]) > HIST_MAX:
            self.server_recent_tat[guild_id][channel_id].pop()
        self.save(properties=True)

    async def get_recent(self, ctx, bot, num=1):
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)
        if guild_id not in self.server_recent_tat.keys():
            self.server_recent_tat[guild_id] = {}
        if channel_id not in self.server_recent_tat[guild_id].keys():
            self.server_recent_tat[guild_id][channel_id] = []
        if len(self.server_recent_tat[guild_id][channel_id]) >= num:
            return self.server_recent_tat[guild_id][channel_id][:num]
        else:
            count = 0
            messages = await ctx.channel.history(limit=MESSAGE_LIMIT).flatten()
            initial_length = len(self.server_recent_tat[guild_id][channel_id])
            def match_tat(text):
                tat = True
                for line in text.split('\n'):
                    tat &= (grapheme.slice(line, 4, 5) == ' ' and grapheme.length(line) == 9)
                return tat
            for msg in messages:
                if msg.author.id == bot.id and match_tat(msg.content):
                    if count >= initial_length:
                        self.server_recent_tat[guild_id][channel_id].append(msg.content)
                    else:
                        if msg.content in self.server_recent_tat[guild_id][channel_id]:
                            count += 1
                if len(self.server_recent_tat[guild_id][channel_id]) >= num:
                    return self.server_recent_tat[guild_id][channel_id][:num]
            return self.server_recent_tat[guild_id][channel_id]

    def get_server_max_hands(self, guild_id):
        guild_id = str(guild_id)

        out = self.server_max_hands.get(guild_id)
        if out is None:
            out = self.server_max_hands[guild_id] = MAX_HAND_SETS
        return out

    def set_server_max_hands(self, guild_id, amt):
        guild_id = str(guild_id)
        self.server_max_hands[guild_id] = amt
        self.save(properties=True)

    def enable(self, guild_id, channel_id):
        guild_id = str(guild_id)
        channel_id = str(channel_id)
        if channel_id is None:
            self.server_disabled[guild_id].clear()
        else:
            del self.server_disabled[guild_id][channel_id]
        self.save(properties=True)

    def disable(self, guild_id, channel_id, length):
        guild_id = str(guild_id)
        channel_id = str(channel_id)
        self.server_disabled[guild_id][channel_id] = length
        self.save(properties=True)

    def save(self, tweets=False, properties=False):
        asyncio.create_task(self.save_help(tweets=tweets, properties=properties))


    async def save_help(self, tweets=False, properties=False):

        files = {}
        if tweets:
            tweets_string = json.dumps({
                'tweets': self.tweets,
                'latest': self.latest.strftime(TWITTER_TIME_FORMAT)
            }, indent=2)
            files['tweet-bin.json'] = {'content': tweets_string}
        if properties:
            properties_string = json.dumps({
                'server_max_hands': self.server_max_hands,
                'server_recent_tat': self.server_recent_tat,
                'server_disabled': self.server_disabled
            }, indent=2)
            files['properties.json'] = {'content': properties_string}
        GIST.edit(files=files)

