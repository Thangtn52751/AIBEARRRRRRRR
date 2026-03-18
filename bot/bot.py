import discord
from discord.ext import commands
from dotenv import load_dotenv
from ai.llm_client import ask_ai
import asyncio
from ai.llm_client import ask_ai_with_image
from bot.user_context import build_message_context, load_user_profiles
import os

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True


class BoBeoBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        with open("data/personality.txt", "r", encoding="utf-8") as f:
            self.personality = f.read()
        self.user_profiles = load_user_profiles()
        self.guild_id = os.getenv("DISCORD_GUILD_ID")

    async def setup_hook(self) -> None:
        await load_commands(self)

        if self.guild_id:
            try:
                guild = discord.Object(id=int(self.guild_id))
            except ValueError:
                print(f"Invalid DISCORD_GUILD_ID: {self.guild_id!r}. Falling back to global sync.")
            else:
                try:
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    print(
                        f"Synced {len(synced)} guild slash commands to {self.guild_id}: "
                        f"{[cmd.name for cmd in synced]}"
                    )
                    return
                except discord.Forbidden:
                    print(
                        "Missing access to the configured guild while syncing slash commands. "
                        f"Check that the bot is in guild {self.guild_id} and invited with "
                        "'applications.commands'. Falling back to global sync."
                    )

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global slash commands: {[cmd.name for cmd in synced]}")

    def get_invite_url(self) -> str | None:
        client_id = self.application_id or (self.user.id if self.user else None)
        if not client_id:
            return None

        permissions = discord.Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True
        )
        return discord.utils.oauth_url(
            client_id,
            permissions=permissions,
            scopes=("bot", "applications.commands")
        )


bot = BoBeoBot()


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    invite_url = bot.get_invite_url()
    if invite_url:
        print(f"Invite URL: {invite_url}")

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if bot.user in message.mentions:

        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        user_context = build_message_context(
            message.author,
            content,
            list(message.mentions),
            bot.user,
            bot.user_profiles
        )

        try:

            async with message.channel.typing():

                # nếu user gửi ảnh
                if message.attachments:

                    image_url = message.attachments[0].url

                    response = await asyncio.to_thread(
                        ask_ai_with_image,
                        bot.personality,
                        content,
                        image_url,
                        user_context
                    )

                else:
                    response = await asyncio.to_thread(
                        ask_ai,
                        bot.personality,
                        content,
                        user_context
                    )

            await message.channel.send(response)

        except Exception as e:
            print("ERROR:", e)
            await message.channel.send("AI error occurred.")

    await bot.process_commands(message)

async def load_commands(bot):

    for filename in os.listdir("./bot/commands"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"bot.commands.{filename[:-3]}")
