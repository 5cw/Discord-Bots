"""
Helper to turn your tweet.js into usable .json.
remove window.YTD.tweet.part0 = at beginning.
"""

import json
from dotenv import load_dotenv
import datetime
from constants import TWITTER_TIME_FORMAT

load_dotenv()


tweets = {}
latest = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(0)))

for data in json.load(open("/Users/lxi/Downloads/twitter-2021-11-24-8e82e6a0926c6224f166c71e21cbfb0fc5575f2f1f5975794276a44abf6ad652/data/lexi-tweet.js")):

    tweet = data['tweet']
    tweets[tweet['id']] = {
        'time': tweet['created_at'],
        'text': tweet['full_text']
    }
    t = datetime.datetime.strptime(tweet['created_at'], TWITTER_TIME_FORMAT)
    if t > latest:
        latest = t


save = {
    'tweets': tweets,
    'latest': latest.strftime(TWITTER_TIME_FORMAT)
}
json.dump(save, open("tweet-bin.json", 'w'), indent=2)
