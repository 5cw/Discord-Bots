import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ['KNUC_TATS_BOT_TOKEN']


TWT_API_KEY = os.environ["TWT_API_KEY"]
TWT_API_SECRET = os.environ["TWT_API_SECRET"]
TWT_ACCESS_TOKEN = os.environ["TWT_ACCESS_TOKEN"]
TWT_ACCESS_SECRET = os.environ["TWT_ACCESS_SECRET"]

KNUC_TATS_LOGIN_USERS = [int(i) for i in os.environ['KNUC_TATS_LOGIN_USERS'].split(',')]
bw_string = os.environ.get('BANNED_WORDS')
if bw_string is None:
    BANNED_WORDS = []
else:
    BANNED_WORDS = bw_string.split(',')

max_string = os.environ.get('MAX_HAND_SETS')

if max_string is None:
    MAX_HAND_SETS = 2
else:
    MAX_HAND_SETS = int(max_string)

PREFIXES = "$!%"

TIME_DICT = {
    's': 1,
    'm': 60
}
TIME_DICT['h'] = 60 * TIME_DICT['m']
TIME_DICT['d'] = 24 * TIME_DICT['h']
TIME_DICT['w'] = 7 * TIME_DICT['d']
TIME_DICT['y'] = 365 * TIME_DICT['d']

THOUSAND_YEARS_IN_SECS = TIME_DICT["y"] * 1000