import datetime
import html
import grapheme
from discord.ext import commands, tasks
from knuc_tats_cog import KnucTatsCog, KnucTats
from constants import KNUC_TATS_LOGIN_USERS, TWT_BEARER_TOKEN, TWT_API_KEY, TWT_API_SECRET, TWT_ACCESS_TOKEN, \
    TWT_ACCESS_SECRET, TWITTER_TIME_FORMAT, HIST_DEFAULT, HIST_MAX
from error_handler import BadWordError, FlagError
from typing import Optional, get_args, get_origin
import tweepy
import re

SKIP = '-s'
DUPES = '-d'
DROP = '-dd'
BAD_WORDS = '-o'
HIST = '-h'
HIST_ALL = '-ha'

TWEET_FLAGS = {
    SKIP: bool,
    DUPES: bool,
    DROP: bool,
    BAD_WORDS: bool,
    HIST: int,
    HIST_ALL: Optional[int]
}

CHECK_FLAGS = {
    HIST: int,
    HIST_ALL: Optional[int]
}


def extract_flags(args, flag_types):
    out = {}

    for flag, type_of in flag_types.items():
        if type_of == bool:
            if flag in args:
                args.remove(flag)
                out[flag] = True
            else:
                out[flag] = False
        else:
            if flag in args:
                index = args.index()
                optional = False
                error = None
                if get_origin(type_of) == Optional:
                    type_of = get_args(type_of)[0]
                    optional = True
                try:
                    if index + 1 < len(args):
                        out[flag] = type_of(args[index + 1])
                    else:
                        error = f"{flag} requires an argument."
                except ValueError or TypeError:
                    error = f"Malformed argument for {flag}."
                if error and not optional:
                    raise FlagError(error)
                elif optional and error:
                    out[flag] = True
                    del args[index]
                else:
                    del args[index]
                    del args[index + 1]
            else:
                out[flag] = None

    return ''.join(args), out


async def drop_bad_words(ctx, tats):
    num_bad_words_dropped = 0
    for i in range(len(tats) - 1, -1, -1):
        if tats[i].is_bad_word:
            num_bad_words_dropped += 1
            del tats[i]
    if len(tats) == 0:
        raise BadWordError("All" if num_bad_words_dropped > 1 else "Your")
    elif num_bad_words_dropped > 0:
        await ctx.send(f"{num_bad_words_dropped} tats were dropped for containing offensive words.")
    return tats


class Twitter(KnucTatsCog):

    def __init__(self, bot, cache):
        super(Twitter, self).__init__(bot, cache)
        client = tweepy.Client(TWT_BEARER_TOKEN, TWT_API_KEY, TWT_API_SECRET, TWT_ACCESS_TOKEN, TWT_ACCESS_SECRET,
                               wait_on_rate_limit=True, return_type=dict)
        user = client.get_user(id=TWT_ACCESS_TOKEN.split('-')[0])
        self.USERNAME = user['data']['username']
        self.ID = user['data']['id']
        self.client = client
        self.tweet_update_loop.start()

    @commands.command(name="dds", help='Alias of %tweet -dd -s',
                      usage='(knuc tats) to tweet text in command, leave blank to tweet most recent tat in channel,')
    async def dds(self, ctx, *, raw=""):
        await self.tweet(ctx, raw=" -dd -s " + raw)

    @commands.command(name="tweet", help='People with the knuc tats login use to tweet most recent tat',
                      usage='(knuc tats) to tweet text in command, leave blank to tweet most recent tat in channel, \n'
                            '-s to skip confirmation, \n'
                            '-d to print check for duplicates, \n'
                            '-dd to drop duplicates, \n'
                            '-o to override bad word check'
                            '-h [distance] to choose the distanceth knuc tats backward, \n'
                            f'-ha (distance) to pick from a table of recent tats. (defaults to {HIST_DEFAULT})\n'
                            'Only users known to have twitter login may use. '
                            'User IDs are hardcoded into bot, check with lexi if you want your discord ID added.')
    async def tweet(self, ctx, *, raw=None):

        if ctx.author.id not in KNUC_TATS_LOGIN_USERS:
            return

        args = []

        if raw is not None:
            args = raw.split()

        cmd_text, flags = extract_flags(args, TWEET_FLAGS)

        skip = flags[SKIP]
        dupes = flags[DUPES]
        drop = flags[DROP]
        bad_words = flags[BAD_WORDS]

        to_tweet = await self.get_selected_tats(ctx, cmd_text, flags)
        if to_tweet is None:
            return

        to_tweet = [tweet for tweet in to_tweet if not len(tweet.text) > 240]
        tats_display = "\n\n"

        if dupes or drop:
            with_drops = await self.check_tweets(ctx, to_tweet, dupes, drop)
            if drop:
                to_tweet = with_drops

        if not bad_words:
            to_tweet = await drop_bad_words(ctx, to_tweet)

        if not dupes:
            tats_display = "\n"
            for tweet in to_tweet:
                if tweet.is_bad_word:
                    tats_display += f'The following tats have been flagged as containing offensive words, ' \
                                    f'which has been overridden with {BAD_WORDS}. Be careful.\n'
                tats_display += '> ' + '\n> '.join(tweet.text.split('\n')) + '\n\n'

        to_tweet.sort(key=lambda t: t.is_bad_word)

        if len(to_tweet) == 0:
            await ctx.send("No knuc tats to tweet")
            return

        tats_display = tats_display[:-2]

        this_plural = 'this' if len(to_tweet) == 1 else 'these'

        if (not skip) or bad_words:  # don't want to allow someone to skip
            await ctx.send(f"You want to tweet {this_plural}? (y/n)" + tats_display)
            confirm = (await self.bot.wait_for('message', check=lambda
                    message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
        else:
            confirm = 'y'

        if confirm and confirm.lower()[0] == 'y':
            for tw in to_tweet:
                if bad_words and tw.is_bad_word:
                    await ctx.send(f"> {tw.text}\nhas been flagged as having offensive words in it, "
                                   f"if you're sure you wish to tweet this, type \"confirm\" now.")
                    bad_word_confirm = (await self.bot.wait_for('message', check=lambda
                        message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
                    if bad_word_confirm.lower() != "confirm":
                        break

                try:
                    response = self.client.create_tweet(text=tw.text)
                    await ctx.send(
                        f"Tweet successful!\nhttps://twitter.com/{self.USERNAME}/status/{response['data']['id']}")
                except tweepy.TweepyException as e:
                    print(e)
                    await ctx.send(f"Tweet failed. Error code: {e}")
            else:
                return
        await ctx.send("Tweet cancelled.")

    @commands.command(name="check", help='Use to see if a knuc tat was posted on the twitter.',
                      usage='(knuc tats) to send a list of tweets containing the tats, '
                            'leave blank to check the most recent tat in the channel.\n'
                            '-h [distance] to choose the distanceth knuc tats backward, \n'
                            f'-ha (distance) to pick from a table of recent tats. (defaults to {HIST_DEFAULT})')
    async def check(self, ctx, *, raw=None):
        args = []
        if raw is not None:
            args = raw.split()
        cmd_text, flags = extract_flags(args, CHECK_FLAGS)

        to_check = await self.get_selected_tats(ctx, cmd_text, flags)
        to_check = [t for t in to_check if not t.is_bad_word]
        if to_check is None:
            return

        await self.check_tweets(ctx, to_check)

    @tasks.loop(minutes=5)
    async def tweet_update_loop(self):
        self.update_tweets()

    def did_tweet(self, tats):
        self.update_tweets()
        if tats not in self.cache.tweets.keys():
            return []
        return [f"https://twitter.com/{self.USERNAME}/status/{tweet['id']}" for tweet in self.cache.tweets[tats]]

    async def check_tweets(self, ctx, tats, prnt=True, drop=False):
        untweeted = []
        for tat in tats:
            tweets = self.did_tweet(tat.text)
            if not tweets:
                if prnt:
                    await ctx.send(f"@{self.USERNAME} has never tweeted \n>>> {tat.text}")
                untweeted.append(tat)
            elif prnt:
                plural = "s" if len(tweets) != 1 else ""
                block = tat.text.replace('\n', '\n> ')
                fmt_tweets = "\n".join(tweets)
                await ctx.send(f"{self.USERNAME} has tweeted \n> "
                               f"{block} \n"
                               f"{len(tweets)} time{plural}.\n"
                               f"{fmt_tweets}")
                if drop:
                    await ctx.send("Dropping.")

        num_dropped = len(tats) - len(untweeted)
        if num_dropped > 0 and not prnt:
            plural = "s" if num_dropped != 1 else ""
            ctx.send(f"Dropped {num_dropped} duplicate{plural}.")
        return untweeted

    def update_tweets(self):
        next_token = None
        more = True
        latest_plus = (self.cache.latest + datetime.timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        def get_clean(text):
            if text[:3] == "RT ":
                text = text[3:]
            text = re.sub(r"(?:@|https://t\.co/)[^\s]+", "", text)
            text = re.sub(r" *\n *", "\n", text)
            text = re.sub(r" +|\t", " ", text)
            text = re.sub(r"^\s|\s$", "", text)
            text = html.unescape(text)
            check = 9
            while grapheme.length(text) > check:
                if grapheme.slice(text, check, check + 1) == " ":
                    text = grapheme.slice(text, None, check) + "\n" + grapheme.slice(text, check + 1, None)
                check += 10
            return text

        while more:
            resp = self.client.get_users_tweets(self.ID,
                                                start_time=latest_plus,
                                                tweet_fields="created_at",
                                                pagination_token=next_token,
                                                max_results=100)
            data = resp.get('data')
            if data is None and next_token is None:
                return
            next_token = resp['meta'].get('next_token')
            if next_token is None:
                more = False
            for tweet in data:
                dt = datetime.datetime.fromisoformat(tweet['created_at'].replace('Z', "+00:00"))
                clean = get_clean(tweet['text'])
                if clean not in self.cache.tweets.keys():
                    self.cache.tweets[clean] = []
                self.cache.tweets[clean].append({
                    'id': tweet['id'],
                    'time': dt.strftime(TWITTER_TIME_FORMAT),
                    'raw': tweet['text']
                })
                if dt > self.cache.latest:
                    self.cache.latest = dt

        self.cache.save(tweets=True)

    async def get_selected_tats(self, ctx, cmd_text, flags):
        if cmd_text != "":
            cmd_tats = self.batch_check_and_format(ctx.message, cmd_text)
            if len(cmd_tats) > 0:
                return cmd_tats
            else:
                ctx.send("Not valid knuc tats.")
                return None

        if ctx.message.reference is not None:
            reply = ctx.message.reference.cached_message
            if reply is None:
                reply = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            reply_tats = self.batch_check_and_format(reply)
            if len(reply_tats) > 0:
                return reply_tats

        recents = await self.history_user_input(ctx, flags[HIST], flags[HIST_ALL])
        if len(recents) > 0:
            return recents

        return None

    async def history_user_input(self, ctx, hist_flag, all_flag):
        if all_flag is not None:
            if type(all_flag) != int:
                hist = HIST_DEFAULT
            elif all_flag < 1:
                hist = 1
            elif all_flag > HIST_MAX:
                hist = HIST_MAX
            else:
                hist = all_flag
        elif hist_flag is not None:
            hist = hist_flag
        else:
            hist = 1

        selected = []

        possible = await self.cache.get_recent(ctx, self.bot.user, hist)
        if all_flag:
            h_string = ''
            for i, tats in enumerate(possible):
                h_string += f'> {i + 1:2}. '
                h_string += '\n>      '.join(tats.split('\n')) + '\n'
            h_string = h_string[:-1]
            await ctx.send(h_string)
            await ctx.send('Send comma-separated list of numbered tats to choose. '
                           '(i.e. 2, 3, 4), or send "all" to select all.')

            confirm = (await self.bot.wait_for('message', check=lambda
                message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
            confirm = re.sub(r'\s', '', confirm)
            if confirm == 'all':
                selected.extend(possible)
            else:
                tat_nums = confirm.split(',')
                for tat_num in tat_nums:
                    try:
                        selected.append(possible[int(tat_num) - 1])
                    except ValueError or IndexError:
                        raise FlagError("Invalid selection.")
        else:
            if possible:
                selected.append(possible[-1])
        return [KnucTats(s, False) for s in selected]
