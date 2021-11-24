import datetime
from discord.ext import commands, tasks
from knuc_tats_cog import KnucTatsCog
from constants import KNUC_TATS_LOGIN_USERS, TWT_BEARER_TOKEN, TWT_API_KEY, TWT_API_SECRET, TWT_ACCESS_TOKEN, \
    TWT_ACCESS_SECRET, TWITTER_TIME_FORMAT
import tweepy
import json




class Twitter(KnucTatsCog):

    def __init__(self, bot):
        super(Twitter, self).__init__(bot)
        client = tweepy.Client(TWT_BEARER_TOKEN, TWT_API_KEY, TWT_API_SECRET, TWT_ACCESS_TOKEN, TWT_ACCESS_SECRET,
                               wait_on_rate_limit=True, return_type=dict)
        user = client.get_user(id=TWT_ACCESS_TOKEN.split('-')[0])
        self.USERNAME = user['data']['username']
        self.ID = user['data']['id']
        self.client = client
        self.tweets = None
        self.latest = None
        self.fetch_tweets()
        self.tweet_update_loop.start()

    @commands.command(name="tweet", help='People with the knuc tats login use to tweet most recent tat',
                      usage='to tweet most recent tat in channel, -s to skip confirmation, -d to check for duplicates.'
                            'Only users known to have twitter login may use. '
                            'User IDs are hardcoded into bot, check with lexi if you want your discord ID added.')
    async def tweet(self, ctx, *args):
        args = list(args)
        if ctx.author.id not in KNUC_TATS_LOGIN_USERS:
            return
        to_tweet = self.get_recent(ctx)


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

        if args:
            potential = self.format_knuc_tats(ctx.message, "".join(args))
            if potential is not None:
                to_tweet = potential

        if to_tweet is None:
            await ctx.send("No knuc tats have been sent in this channel since the bot was last restarted.")
            return
        if len(to_tweet) > 240:
            await ctx.send("Too many characters to tweet.")
            return


        if dupes:
            await self.check_tweets(ctx, to_tweet)

        if not skip:
            await ctx.send(f"You want to tweet this? (y/n)\n>>> {to_tweet}")
            confirm = (await self.bot.wait_for('message', check=lambda
                message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
        else:
            confirm = 'y'
        if confirm and confirm.lower()[0] == 'y':
            try:
                response = self.client.create_tweet(text=to_tweet)
                await ctx.send(f"Tweet successful!\nhttps://twitter.com/{self.USERNAME}/status/{response['data']['id']}")
            except tweepy.TweepyException as e:
                print(e)
                await ctx.send(f"Tweet failed. Error code: {e}")
        else:
            await ctx.send("Tweet cancelled.")

    @commands.command(name="check", help='Use to see if a knuc tat was posted on the twitter.',
                      usage='to send a list of tweets containing the most recent tat in the server.')
    async def check(self, ctx, *args):
        to_check = self.get_recent(ctx)
        if args:
            potential = self.format_knuc_tats(ctx.message, "".join(args))
            if potential is not None:
                to_check = potential
        if to_check is None:
            await ctx.send("No knuc tats have been sent in this channel since the bot was last restarted.")
            return
        await self.check_tweets(ctx, to_check)

    @tasks.loop(hours=4)
    async def tweet_update_loop(self):
        self.update_tweets()

    def did_tweet(self, tats):
        self.update_tweets()
        out = []
        for id, tweet in self.tweets.items():
            if tats in tweet['text']:
                out.append(f"https://twitter.com/{self.USERNAME}/status/{id}")
        return out

    async def check_tweets(self, ctx, tats):
        tweets = self.did_tweet(tats)
        if not tweets:
            await ctx.send(f"@{self.USERNAME} has never tweeted \n>>> {tats}")
            return
        plural = "s" if len(tweets) != 1 else ""
        block = tats.replace('\n', '\n> ')
        fmt_tweets = "\n".join(tweets)
        await ctx.send(f"{self.USERNAME} has tweeted \n> "
                       f"{block} \n"
                       f"{len(tweets)} time{plural}.\n"
                       f"{fmt_tweets}")

    def update_tweets(self):
        next_token = None
        more = True
        latest_plus = (self.latest + datetime.timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
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
                self.tweets[tweet['id']] = {
                    'time': dt.strftime(TWITTER_TIME_FORMAT),
                    'text': tweet['text']
                }
                if dt > self.latest:
                    self.latest = dt

        self.save_tweets()


    def fetch_tweets(self):
        s = self.fetch()
        data = json.loads(s)
        self.tweets = data['tweets']
        self.latest = datetime.datetime.strptime(data['latest'], TWITTER_TIME_FORMAT)


    def save_tweets(self):
        out = json.dumps({
            'tweets': self.tweets,
            'latest': self.latest.strftime(TWITTER_TIME_FORMAT)
        }, indent=2)
        self.save(tweets=out)
