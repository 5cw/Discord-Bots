from errors import UnknownAPIError, UserBannedError
from constants import JSON_CREDS, SCOPES, SPREADSHEET_ID, BALANCE_SHEET_NAME, BTS_SHEET_NAME
import gspread
import dotenv
from decimal import *
import asyncio
import os.path

dotenv.load_dotenv()

MAX_DIGITS = int(os.environ['MAX_DIGITS'])
getcontext().prec = MAX_DIGITS + 5

class Cache:
    def __init__(self):
        self.gc = gspread.service_account_from_dict(info=JSON_CREDS, scopes=SCOPES)
        self.sh = self.gc.open_by_key(SPREADSHEET_ID)
        self.MAX_BALANCE = Decimal("10") ** Decimal(MAX_DIGITS)
        self.rate_limited = False
        self.ids = None
        self.names = None
        self.balances = None
        self.banned = None
        self.user_locks = None

    async def fetch_cache(self):
        batch_get = (await self.rate_limit_retry(self.sh.values_batch_get,
                                                 [f"{BALANCE_SHEET_NAME}!A:B", f"{BTS_SHEET_NAME}!A:A", f"{BTS_SHEET_NAME}!B:B"],
                                                 {"majorDimension": "COLUMNS"}))["valueRanges"]
        ids = batch_get[1].get('values') or [[]]
        self.ids = [int(id) for id in ids[0]]
        name_bals = batch_get[0].get('values') or [[], []]
        self.names = name_bals[0]
        self.balances = [Decimal(num) for num in name_bals[1]]
        banned = batch_get[2].get('values') or [[]]
        self.banned = [int(id) for id in banned[0]]
        self.user_locks = {i: asyncio.Lock() for i in self.ids}

    async def push_cache(self, ban=False, unban=False):
        data = []
        names = self.names
        balances = [f"{bal:.2f}" for bal in self.balances]
        ids = [str(id) for id in self.ids]
        banned = [str(id) for id in self.banned]
        if len(ids) > 0:
            data.append({
                'range': f"{BALANCE_SHEET_NAME}!A1:B{len(ids)}",
                "majorDimension": "COLUMNS",
                "values": [names, balances]
            })
            data.append({
                'range': f"{BTS_SHEET_NAME}!A1:A{len(ids)}",
                "majorDimension": "COLUMNS",
                "values": [ids]
            })
        if len(banned) > 0:
            data.append({
                'range': f"{BTS_SHEET_NAME}!B1:B{len(banned)}",
                "majorDimension": "COLUMNS",
                "values": [banned]
            })
        params = {
            "valueInputOption": "RAW",
        }
        body = {
            "data": data
        }
        await self.lock()
        await self.rate_limit_retry(self.sh.values_batch_update, params, body)
        if ban:
            await self.rate_limit_retry(self.sh.values_batch_clear,
                                        body={"ranges": [f"{BALANCE_SHEET_NAME}!A{len(ids) + 1}:B{len(ids) + 1}",
                                                         f"{BTS_SHEET_NAME}!A{len(ids) + 1}:A{len(ids) + 1}"]})
        elif unban:
            await self.rate_limit_retry(self.sh.values_batch_clear,
                                        body={"ranges": [f"{BTS_SHEET_NAME}!B{len(banned) + 1}:B{len(banned) + 1}"]})
        self.unlock()

    async def rate_limit_retry(self, f, *args, **kwargs):
        s = True
        timeout = 1
        while s:
            resp = f(*args, **kwargs)
            s = False
            if resp.get("error"):
                if resp["error"]["code"] == 429:
                    s = True
                else:
                    raise UnknownAPIError()
            self.rate_limited = s
            if s:
                await asyncio.sleep(timeout)
                timeout *= 2
            else:
                return resp

    async def lock(self, user=None):
        if user is None:
            for l in self.user_locks.values():
                await l.acquire()
            return
        out = self.user_locks.get(user.id)
        if out is None:
            self.new_user(user)
            out = self.user_locks.get(user.id)
        await out.acquire()

    def unlock(self, user=None):
        if user is None:
            for l in self.user_locks.values():
                l.release()
            return
        self.user_locks[user.id].release()

    async def set_name(self, user, name):
        await self.lock(user)
        self.names[self.user_index(user)] = name
        self.unlock(user)

    async def get_name(self, user):
        await self.lock(user)
        out = self.names[self.user_index(user)]
        self.unlock(user)
        return out

    async def set_balance(self, user, new_balance):
        await self.lock(user)
        idx = self.user_index(user)
        self.balances[idx] = new_balance
        self.unlock(user)

    async def get_balance(self, user):
        await self.lock(user)
        idx = self.user_index(user)
        out = self.balances[idx]
        self.unlock(user)
        return out

    def user_index(self, user):
        try:
            idx = self.ids.index(user.id)
        except ValueError:
            self.new_user(user)
            idx = self.ids.index(user.id)
        return idx

    def new_user(self, user):
        if user.id in self.banned:
            raise UserBannedError
        self.ids.append(user.id)
        self.names.append(str(user))
        self.balances.append(Decimal("25.00"))
        self.user_locks[user.id] = asyncio.Lock()

    async def ban(self, ban_user):
        await self.lock()
        self.banned.append(ban_user.id)
        if ban_user.id in self.ids:
            idx = self.user_index(ban_user)
            del self.ids[idx]
            del self.balances[idx]
            del self.names[idx]
            del self.user_locks[ban_user.id]
        self.unlock()

    async def unban(self, ban_user):
        await self.lock()
        self.banned.remove(ban_user.id)
        self.unlock()

