from dotenv import load_dotenv
import os
import json
import sys

load_dotenv()
CURRENCY_NAME = os.environ["CURRENCY_NAME"]
PLURAL_CURRENCY_NAME = os.environ.get("PLURAL_CURRENCY_NAME")
if PLURAL_CURRENCY_NAME is None:
    PLURAL_CURRENCY_NAME = CURRENCY_NAME + 's'
TOKEN = os.environ["CURRENCY_BOT_TOKEN"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
BALANCE_SHEET_NAME = os.environ["BALANCE_SHEET_NAME"]
BTS_SHEET_NAME = os.environ["BTS_SHEET_NAME"]
MAX_DIGITS = int(os.environ["MAX_DIGITS"])
JSON_FILE = os.environ.get("JSON_FILE")
if JSON_FILE is None:
    JSON_TEXT = os.environ["JSON_TEXT"]
    JSON_CREDS = json.loads(JSON_TEXT)
else:
    JSON_CREDS = json.load(open(os.path.dirname(sys.argv[0]) + "/" + JSON_FILE))

SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"]
