import discord
from discord import app_commands
from discord.ext import commands


class Sync(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="sync",
        description="Đồng bộ lại splash command trong server."
    )
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Lệnh này chỉ được dùng trong server Tấu hài cùng bo béo.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = discord.Object(id=interaction.guild.id)
        self.bot.tree.copy_global_to(guild=guild)
        synced = await self.bot.tree.sync(guild=guild)

        await interaction.followup.send(
            f"Đã đồng bộ {len(synced)} slash command cho server này.",
            ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sync(bot))
