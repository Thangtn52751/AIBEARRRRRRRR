import discord
from discord.ext import commands
from dotenv import load_dotenv
from ai.llm_client import ask_ai, ask_ai_with_image, detect_mood
import asyncio
from bot.user_context import build_message_context, load_user_profiles
from memory.conversation import ConversationMemory
import os
from pathlib import Path

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
BOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BOT_DIR.parent
DEFAULT_PERSONALITY_PATH = BOT_DIR / "personality.txt"
DATA_PERSONALITY_PATH = PROJECT_ROOT / "data" / "personality.txt"


class BoBeoBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        personality_path = DATA_PERSONALITY_PATH
        if not personality_path.exists():
            personality_path = DEFAULT_PERSONALITY_PATH

        with personality_path.open("r", encoding="utf-8") as f:
            self.personality = f.read()
        self.user_profiles = load_user_profiles()
        self.conversation_memory = ConversationMemory()
        self.user_states: dict[str, dict[str, str]] = {}
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
            read_message_history=True,
            mention_everyone=True
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
        user_id = str(message.author.id)
        recent_messages = bot.conversation_memory.get_recent_user_messages(user_id)
        mood_state = await asyncio.to_thread(detect_mood, content, recent_messages)
        bot.user_states[user_id] = mood_state
        user_context = build_message_context(
            message.author,
            list(message.mentions),
            bot.user,
            bot.user_profiles,
            mood_state
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

            stored_user_message = content
            if not stored_user_message:
                stored_user_message = "[image attachment]" if message.attachments else "[empty]"

            bot.conversation_memory.add(user_id, "user", stored_user_message)
            bot.conversation_memory.add(user_id, "assistant", response)
            await message.channel.send(response)

        except Exception as e:
            print("ERROR:", e)
            await message.channel.send("AI error occurred.")

    await bot.process_commands(message)

async def load_commands(bot):
    commands_dir = BOT_DIR / "commands"

    for command_file in commands_dir.glob("*.py"):
        if command_file.name != "__init__.py":
            await bot.load_extension(f"bot.commands.{command_file.stem}")
