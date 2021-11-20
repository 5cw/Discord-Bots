# Currency Bot
### Bot to manage the currency on your discord server in a spreadsheet.

Built on python 3.8.12, no guarantees on other versions.

Necessary files:
* [currency_bot.py](currency_bot.py) (file to run)
* [cache.py](cache.py)

Dependencies:
* [gspread](https://docs.gspread.org/en/latest/)
* [discord](https://discordpy.readthedocs.io/en/stable/)
* [python-dotenv](https://pypi.org/project/python-dotenv/)

Environment variables:
```
required
C_TOKEN=Discord Bot Token
CURRENCY_NAME=My Currency Name
MAX_DIGITS=100 or whatever number you want
SPREADSHEET_ID=Google Sheets ID
either
JSON=Google_Sheets_API_Creds.json
or
JSON_TEXT={Google Sheets API Creds JSON string}

optional
PLURAL_CURRENCY_NAME=My Currency Name Plural (if plural is something other than adding an s.)
```
Environment variables can go in a .env file, or in the environment variables section of a hosting service (like [heroku](https://heroku.com).)

Some of this information is sensitive, so be careful where you put a .env file.

You will need to enable the [Google Sheets API.](https://developers.google.com/workspace/guides/create-project)