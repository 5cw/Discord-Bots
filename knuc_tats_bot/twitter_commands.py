import datetime
from discord.ext import commands, tasks
from knuc_tats_cog import KnucTatsCog
from constants import KNUC_TATS_LOGIN_USERS, TWT_BEARER_TOKEN, TWT_API_KEY, TWT_API_SECRET, TWT_ACCESS_TOKEN, \
    TWT_ACCESS_SECRET, TWITTER_TIME_FORMAT, HIST_NUM, HIST_MAX, TIME_ZONE
import tweepy
import re
from datetime import datetime, timedelta


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

    @commands.command(name="tweet", help='People with the knuc tats login use to tweet most recent tat',
                      usage='(knuc tats) to tweet text in command, leave blank to tweet most recent tat in channel, \n'
                            '-s to Skip confirmation, \n'
                            '-d to print check for Duplicates, \n'
                            '-dd to Drop Duplicates, \n'
                            '-f to schedule Future tats \n'
                            '-b [distance] to choose the distanceth knuc tats Backward, \n'
                            f'-t (distance) to pick from a Table of recent tats. (defaults to {HIST_NUM})\n'
                            'Only users known to have twitter login may use. '
                            'User IDs are hardcoded into bot, check with lexi if you want your discord ID added.')
    async def tweet(self, ctx, *, raw=None):

        if ctx.author.id not in KNUC_TATS_LOGIN_USERS:
            return
        skip = dupes = drop = future = False
        args = []
        if raw is not None:
            args = raw.split()
            try:
                args.remove("-s")
                skip = True
            except ValueError:
                skip = False

            try:
                args.remove("-d")
                dupes = True
            except ValueError:
                dupes = False

            try:
                args.remove("-dd")
                drop = True
            except ValueError:
                drop = False

            try:
                args.remove("-f")
                future = True
            except ValueError:
                future = False

        to_tweet = await self.parse_which_tats(ctx, args)
        if to_tweet == None:
            return

        to_tweet = [tweet for tweet in to_tweet if not len(tweet) > 240]
        cond_display = "\n\n"

        if dupes or drop:
            with_drops = await self.check_tweets(ctx, to_tweet, dupes, drop)
            if drop:
                to_tweet = with_drops

        if not dupes:
            cond_display = "\n"
            for tweet in to_tweet:
                cond_display += '> ' + '\n> '.join(tweet.split('\n')) + '\n\n'

        if len(to_tweet) == 0:
            await ctx.send("No knuc tats fit your criteria.")
            return

        date = None
        if future:
            date = self.get_datetime(ctx)
            if date is None:
                return

        cond_display = cond_display[:-2]

        this_plural = 'this' if len(to_tweet) == 1 else 'these'

        if not skip:
            await ctx.send(f"You want to {'schedule' if future else 'tweet'} {this_plural}? (y/n)" + cond_display)
            confirm = (await self.bot.wait_for('message', check=lambda
                message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
        else:
            confirm = 'y'

        if confirm and confirm.lower()[0] == 'y':
            if future:
                self.cache.add_to_schedule(date, to_tweet)
            else:
                await self.tweet_tats(to_tweet, ctx)
            await self.tweet_tats(to_tweet, ctx)
        else:
            await ctx.send("Tweet cancelled.")

    @commands.command(name="check", help='Use to see if a knuc tat was posted on the twitter.',
                      usage='(knuc tats) to send a list of tweets containing the tats, '
                            'leave blank to check the most recent tat in the channel.\n'
                            '-b [distance] to choose the distanceth knuc tats Backward, \n'
                            f'-t (distance) to pick from a Table of recent tats. (defaults to {HIST_NUM})')
    async def check(self, ctx, *, raw=None):
        args = []
        if raw is not None:
            args = raw.split()
        to_check = await self.parse_which_tats(ctx, args)
        if to_check == None:
            return
        if to_check == []:
            await ctx.send("No knuc tats to check.")
            return
        await self.check_tweets(ctx, to_check)

    @tasks.loop(hours=4)
    async def tweet_update_loop(self):
        self.update_tweets()


    def did_tweet(self, tats):
        self.update_tweets()
        out = []
        for id, tweet in self.cache.tweets.items():
            if tats in tweet['text']:
                out.append(f"https://twitter.com/{self.USERNAME}/status/{id}")
        return out

    async def check_tweets(self, ctx, tats, prnt=True, drop=False):
        untweeted = []
        for tat in tats:
            tweets = self.did_tweet(tat)
            if not tweets:
                if prnt:
                    await ctx.send(f"@{self.USERNAME} has never tweeted \n>>> {tat}")
                untweeted.append(tat)
            elif prnt:
                plural = "s" if len(tweets) != 1 else ""
                block = tat.replace('\n', '\n> ')
                fmt_tweets = "\n".join(tweets)
                await ctx.send(f"{self.USERNAME} has tweeted \n> "
                               f"{block} \n"
                               f"{len(tweets)} time{plural}.\n"
                               f"{fmt_tweets}")
                if drop:
                    await ctx.send("Dropping.")
        return untweeted

    def update_tweets(self):
        next_token = None
        more = True
        latest_plus = (self.cache.latest + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
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
                self.cache.tweets[tweet['id']] = {
                    'time': dt.strftime(TWITTER_TIME_FORMAT),
                    'text': tweet['text']
                }
                if dt > self.cache.latest:
                    self.cache.latest = dt

        self.cache.save(tweets=True)

    async def parse_which_tats(self, ctx, args):
        recents = []
        args, hist, all = self.extract_hist_flag(args)
        if type(args) == str:
            await ctx.send(args)
            return None
        cmd_tat = self.format_knuc_tats(ctx.message, ''.join(args))
        if ctx.message.reference is not None:
            reply = ctx.message.reference.cached_message
            if reply is None:
                reply = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            reply_tat = self.format_knuc_tats(reply)
        else:
            reply_tat = None
        possible = None
        if hist > 0:
            possible = await self.cache.get_recent(ctx, self.bot.user, hist)
        elif cmd_tat is not None:
            recents.append(cmd_tat)
        elif reply_tat is not None:
            recents.append(reply_tat)
        else:
            await ctx.send("Not valid knuc tats.")
            return None

        if all:
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
                recents.extend(possible)
            else:
                tat_nums = confirm.split(',')
                for tat_num in tat_nums:
                    try:
                        recents.append(possible[int(tat_num) - 1])
                    except ValueError or IndexError:
                        await ctx.send('Invalid selection.')
                        return None
        else:
            if possible:
                recents.append(possible[-1])
        return recents

    def extract_hist_flag(self, args):
        hist = 1
        hdex = None
        all = None

        if '-b' in args and '-t' in args:
            return 'Cannot set both -b and -t flags', None, None

        if '-b' in args:
            hdex = args.index("-b")
            del args[hdex]
            all = False
        elif '-t' in args:
            hdex = args.index("-t")
            del args[hdex]
            all = True
        elif args != []:
            hist = 0

        if hdex is not None:
            try:
                hist = int(args[hdex])
                del args[hdex]
            except (ValueError, IndexError):
                if all:
                    hist = HIST_NUM
                else:
                    return '-b flag requires number of tats to jump back', None, None
            if args != []:
                return 'Cannot set -b or -t flag with text for knuc tats', None, None

        if hist < 0:
            hist = HIST_NUM

        if hist > HIST_MAX:
            hist = HIST_MAX

        return args, hist, all

    async def tweet_tats(self, to_tweet, ctx):
        for tw in to_tweet:
            try:
                response = self.client.create_tweet(text=tw)
                await ctx.send(
                    f"Tweet successful!\nhttps://twitter.com/{self.USERNAME}/status/{response['data']['id']}")

            except tweepy.TweepyException as e:
                print(e)
                await ctx.send(f"Tweet failed. Error code: {e}")

    async def get_datetime(self, ctx):
        await ctx.send(f"When do you want to schedule?\n"
                       "(m/d/yy or m/d/yyyy or m/d) (h:m:s or h:m or blank)(am/pm or blank)")

        date_str = (await self.bot.wait_for('message', check=lambda
            message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content

        date_formats = ["%m/%d", "%m/%d/%y", "%m/%d/%Y"]
        time_formats = [" %H:%M:%S", " %H:%M", " %I:%M:%S %p", "%I:%M %p", ""]
        date = None
        for df in date_formats:
            if date is not None:
                break
            for tf in time_formats:
                try:
                    date = datetime.strptime(f'{date_str} {TIME_ZONE}', df + tf + " %Z")
                    if df == "%m/%d":
                        date = date.replace(year=datetime.now().year)
                        if date < datetime.now():
                            date = date.replace(year=date.year + 1)
                    break
                except ValueError:
                    pass
        else:
            await ctx.send(f"Date and time could not be parsed.")

        if date < datetime.now():
            await ctx.send(f"Date and time must be in the future.")
            return None

        await ctx.send(date.strftime("Scheduled for %M %d, %Y, at %I:%M%S %p"))

        return date
