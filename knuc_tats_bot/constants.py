import os
import github3
from dotenv import load_dotenv
from obfuscate import obfuscate, OBFUSCATE_TOKEN

load_dotenv()
TOKEN = os.environ['KNUC_TATS_BOT_TOKEN']

TWT_API_KEY = os.environ["TWT_API_KEY"]
TWT_API_SECRET = os.environ["TWT_API_SECRET"]
TWT_ACCESS_TOKEN = os.environ["TWT_ACCESS_TOKEN"]
TWT_ACCESS_SECRET = os.environ["TWT_ACCESS_SECRET"]
TWT_BEARER_TOKEN = os.environ["TWT_BEARER_TOKEN"]

KNUC_TATS_LOGIN_USERS = [int(i) for i in os.environ['KNUC_TATS_LOGIN_USERS'].split(',')]
#uncomment line if you want a decent starting point for banned words
bw_string = os.environ.get('BANNED_WORDS') # or "%41%42%42%4f,%41%42%4f,%43%48%49%4e%41%4d%41%4e,%43%48%49%4e%41%4d%45%4e,%43%48%49%4e%4b,%43%4f%4f%4c%49%45,%45%53%4b%49%4d%4f,%47%4f%4c%4c%49%57%4f%47,%47%4f%4f%4b,%47%59%50,%47%59%50%53%59,%48%45%45%42,%4a%41%50,%4b%41%46%46%45%52,%4b%41%46%46%49%52,%4b%41%46%46%49%52,%4b%41%46%46%52%45,%4b%41%46%49%52,%4b%49%4b%45,%4e%45%47%52%45%53%53,%4e%45%47%52%4f,%4e%49%47,%4e%49%47%2d%4e%4f%47,%4e%49%47%47%41,%4e%49%47%47%45%52,%4e%49%47%47%55%48,%50%41%4a%45%45%54,%50%41%4b%49,%50%49%43%4b%41%4e%49%4e%4e%49%45,%50%49%43%4b%41%4e%49%4e%4e%59,%52%41%47%48%45%41%44,%52%45%54%41%52%44,%53%41%4d%42%4f,%53%50%45%52%47,%53%50%49%43,%53%50%4f%4f%4b,%53%51%55%41%57,%54%41%52%44,%57%45%54%42%41%43%4b,%57%49%47%47%45%52,%5a%4f%47,%52%41%50%45,%52%41%50%49%53%54"
if bw_string is None:
    BANNED_WORDS = []
elif bw_string[0] == OBFUSCATE_TOKEN:
    BANNED_WORDS = bw_string.split(',')
else:
    BANNED_WORDS = [obfuscate(word) for word in bw_string.split(',')]


GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_PASSWORD = os.environ.get("GITHUB_PASSWORD")
GITHUB_GISTS_TOKEN = os.environ.get("GITHUB_GISTS_TOKEN")

max_string = os.environ.get('MAX_HAND_SETS')

MESSAGE_LIMIT = os.environ.get("MESSAGE_LIMIT")

ONE_HAND = os.environ.get("ONE_HAND") or 4
TWO_HANDS = 2 * ONE_HAND


if MESSAGE_LIMIT is None:
    MESSAGE_LIMIT = 200
else:
    MESSAGE_LIMIT = int(MESSAGE_LIMIT)

if max_string is None:
    MAX_HAND_SETS = 2
else:
    MAX_HAND_SETS = int(max_string)

GIST = None
if GITHUB_GISTS_TOKEN:
    gh = github3.login(token=GITHUB_GISTS_TOKEN)
else:
    gh = github3.login(username=GITHUB_USERNAME, password=GITHUB_PASSWORD)
for gist in gh.gists():
    if 'tweet-bin.json' in gist.files.keys():
        GIST = gist
        break
else:
    raise FileNotFoundError

SPLIT = "|"
PREFIXES = "$!%"
HIST_DEFAULT = 5
HIST_MAX = 20

TIME_DICT = {
    's': 1,
    'm': 60
}
TIME_DICT['h'] = 60 * TIME_DICT['m']
TIME_DICT['d'] = 24 * TIME_DICT['h']
TIME_DICT['w'] = 7 * TIME_DICT['d']
TIME_DICT['y'] = 365 * TIME_DICT['d']

THOUSAND_YEARS_IN_SECS = TIME_DICT["y"] * 1000

TWITTER_TIME_FORMAT = "%a %b %d %H:%M:%S %z %Y"
