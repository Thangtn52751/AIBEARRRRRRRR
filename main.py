import os
from dotenv import load_dotenv

load_dotenv()

from bot.bot import bot

TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)
