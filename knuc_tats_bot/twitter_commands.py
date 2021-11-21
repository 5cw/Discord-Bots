from discord.ext import commands
from knuc_tats_cog import KnucTatsCog
from constants import KNUC_TATS_LOGIN_USERS, TWT_API_KEY, TWT_API_SECRET, TWT_ACCESS_TOKEN, TWT_ACCESS_SECRET
import tweepy


class Twitter(KnucTatsCog):

    def __init__(self, bot):
        super(Twitter, self).__init__(bot)
        tw_auth = tweepy.OAuthHandler(TWT_API_KEY, TWT_API_SECRET)
        tw_auth.set_access_token(TWT_ACCESS_TOKEN, TWT_ACCESS_SECRET)
        api = tweepy.API(tw_auth)
        api.verify_credentials()
        self.api = api

    @commands.command(name="tweet", help='People with "knuc tats login" role use to tweet most recent tat',
                    usage='to tweet most recent tat in channel, -s to skip confirmation. '
                          'Only users known to have twitter login may use. '
                          'User IDs are hardcoded into bot, check with lexi if you want your discord ID added.')
    async def tweet(self, ctx, *args):
        if ctx.author.id not in KNUC_TATS_LOGIN_USERS:
            return
        to_tweet = self.get_recent(ctx)
        if to_tweet is None:
            await ctx.send("No knuc tats have been sent in this channel since the bot was last restarted.")
            return
        if len(to_tweet) > 240:
            await ctx.send("Too many characters to tweet.")
            return
        if "-s" not in args:
            await ctx.send(f"You want to tweet this? (y/n)\n>>> {to_tweet}")
            confirm = (await self.bot.wait_for('message', check=lambda
                message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)).content
        else:
            confirm = 'y'
        if confirm and confirm.lower()[0] == 'y':
            try:
                response = self.api.update_status(to_tweet)
                await ctx.send(f"Tweet successful!\nhttps://twitter.com/uvmknuctats/status/{response.id_str}")
            except tweepy.TweepyException as e:
                print(e)
                await ctx.send(f"Tweet failed. Error code: {e}")
        else:
            await ctx.send("Tweet cancelled.")