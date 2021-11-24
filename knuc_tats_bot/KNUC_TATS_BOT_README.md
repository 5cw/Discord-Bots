# Knuc Tats Bot
### Bot to detect knuc tats and tweet them from a connected account. Ours is [@uvmknuctats](https://twitter.com/uvmknuctats).

Built on python 3.8.12, no guarantees on other versions.

Dependencies:
* [tweepy](https://docs.tweepy.org/en/stable/install.html)
* [grapheme](https://pypi.org/project/grapheme/)
* [discord](https://discordpy.readthedocs.io/en/stable/)
* [python-dotenv](https://pypi.org/project/python-dotenv/)

Environment variables:
```
required
KNUC_TATS_BOT_TOKEN=Discord Bot Token
TWT_API_KEY=Twitter Client API Key
TWT_API_SECRET=Twitter Client API Secret
TWT_ACCESS_TOKEN=Twitter Access Token
TWT_ACCESS_SECRET=Twitter Access Secret
TWT_BEARER_TOKEN=Twitter Bearer Token
KNUC_TATS_LOGIN_USERS=comma,separated,list,of,discord,user,ids
either
GITHUB_GISTS_TOKEN=Github Token with repo and gist privilege
or
GITHUB_USERNAME=Github Username
GITHUB_PASSWORD=Github Password

optional
BANNED_WORDS=comma,separated,list,of,banned,words
MAX_HAND_SETS=default maximum number of sets of hands (can be modified per-server, defaults to 2.)
```
Environment variables can go in a .env file, or in the environment variables section of a hosting service (like [heroku](https://heroku.com).)

Some of this information is sensitive, so be careful where you put your .env file.

You'll need a [Twitter developer account.](https://dev.to/sumedhpatkar/beginners-guide-how-to-apply-for-a-twitter-developer-account-1kh7)

You'll need to create a github gist with a file named tweet-bin.json