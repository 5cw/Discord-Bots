import discord
from discord.ext import commands
from constants import TOKEN
from error_handler import ErrorHandler
from message_handler import MessageHandler
from twitter_commands import Twitter
from admin_commands import Admin
from cache import Cache


intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="%", intents=intents, help_command=commands.DefaultHelpCommand(
    no_category='General'
))
cache = Cache()
bot.add_cog(MessageHandler(bot, cache))
bot.add_cog(Admin(bot, cache))
bot.add_cog(Twitter(bot, cache))
bot.add_cog(ErrorHandler(bot, cache))





bot.run(TOKEN)
