import discord
from discord.ext import commands
from constants import TOKEN
from message_handler import MessageHandler
from twitter_commands import Twitter
from admin_commands import Admin


intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="%", intents=intents, help_command=commands.DefaultHelpCommand(
    no_category='General'
))

bot.add_cog(MessageHandler(bot))
bot.add_cog(Admin(bot))
bot.add_cog(Twitter(bot))


@bot.event
async def on_ready():
    print("knuc tats bot ready!")




bot.run(TOKEN)
