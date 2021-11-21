import asyncio
from cache import Cache
from general_commands import General
from admin_commands import Admin
from error_handler import ErrorHandler
from constants import TOKEN
import discord
from discord.ext import commands


intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='$', intents=intents)

cache = Cache()
asyncio.run(cache.fetch_cache())

general = General(bot, cache)

bot.add_cog(general)
bot.add_cog(Admin(bot, cache))
bot.add_cog(ErrorHandler(bot, cache))

bot.help_command.cog = general

bot.run(TOKEN)
