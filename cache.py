import re
import gspread

import discord
from discord.ext import commands
from dotenv import load_dotenv
from decimal import *
import asyncio
import os.path


class UserBannedError(commands.CommandError):
    pass


class DecimalizationError(commands.CommandError):
    def __init__(self, amount):
        super()
        self.amount = amount


class UnknownAPIError(commands.CommandError):
    pass

load_dotenv()
MAX_DIGITS = int(os.getenv('MAX_DIGITS'))
getcontext().prec = MAX_DIGITS + 5

class Cache:
    def __init__(self):
        load_dotenv()
        SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
        SCOPES = os.getenv('SCOPES').split(',')
        JSON = os.getenv('JSON')
        self.gc = gspread.service_account(filename=JSON, scopes=SCOPES)
        self.sh = self.gc.open_by_key(SPREADSHEET_ID)
        self.MAX_BALANCE = Decimal("10") ** Decimal(MAX_DIGITS)
        self.rate_limited = False
        self.ids = None
        self.names = None
        self.balances = None
        self.banned = None
        self.user_locks = None

    async def fetchCache(self):
        batch_get = (await self.rate_limit_retry(self.sh.values_batch_get,
                                                 ["Balances!A:B", "bts!A:A", "bts!B:B"],
                                                 {"majorDimension": "COLUMNS"}))["valueRanges"]
        ids = batch_get[1].get('values') or [[]]
        self.ids = [int(id) for id in ids[0]]
        name_bals = batch_get[0].get('values') or [[], []]
        self.names = name_bals[0]
        self.balances = [Decimal(num) for num in name_bals[1]]
        banned = batch_get[2].get('values') or [[]]
        self.banned = [int(id) for id in banned[0]]
        self.user_locks = {i: asyncio.Lock() for i in self.ids}

    async def pushCache(self, ban=False, unban=False):
        data = []
        names = self.names
        balances = [f"{bal:.2f}" for bal in self.balances]
        ids = [str(id) for id in self.ids]
        banned = [str(id) for id in self.banned]
        if len(ids) > 0:
            data.append({
                'range': f"Balances!A1:B{len(ids)}",
                "majorDimension": "COLUMNS",
                "values": [names, balances]
            })
            data.append({
                'range': f"bts!A1:A{len(ids)}",
                "majorDimension": "COLUMNS",
                "values": [ids]
            })
        if len(banned) > 0:
            data.append({
                'range': f"bts!B1:B{len(banned)}",
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
                                        body={"ranges": [f"Balances!A{len(ids) + 1}:B{len(ids) + 1}",
                                                         f"bts!A{len(ids) + 1}:A{len(ids) + 1}"]})
        elif unban:
            await self.rate_limit_retry(self.sh.values_batch_clear,
                                        body={"ranges": [f"bts!B{len(banned) + 1}:B{len(banned) + 1}"]})
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
            self.newUser(user)
            out = self.user_locks.get(user.id)
        await out.acquire()

    def unlock(self, user=None):
        if user is None:
            for l in self.user_locks.values():
                l.release()
            return
        self.user_locks[user.id].release()

    async def setName(self, user, name):
        await self.lock(user)
        self.names[self.userIndex(user)] = name
        self.unlock(user)

    async def getName(self, user):
        await self.lock(user)
        out = self.names[self.userIndex(user)]
        self.unlock(user)
        return out

    async def setBalance(self, user, new_balance):
        await self.lock(user)
        idx = self.userIndex(user)
        self.balances[idx] = new_balance
        self.unlock(user)

    async def getBalance(self, user):
        await self.lock(user)
        idx = self.userIndex(user)
        out = self.balances[idx]
        self.unlock(user)
        return out

    def userIndex(self, user):
        try:
            idx = self.ids.index(user.id)
        except ValueError:
            self.newUser(user)
            idx = self.ids.index(user.id)
        return idx

    def newUser(self, user):
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
            idx = self.userIndex(ban_user)
            del self.ids[idx]
            del self.balances[idx]
            del self.names[idx]
            del self.user_locks[ban_user.id]
        self.unlock()

    async def unban(self, ban_user):
        await self.lock()
        self.banned.remove(ban_user.id)
        self.unlock()
