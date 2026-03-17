import discord
from discord import app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Kiểm tra độ trễ của bot."
    )
    async def ping(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Độ trễ của bot: **{latency}ms**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📡 Kết nối",
            value="Bot đang hoạt động bình thường.",
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.set_footer(
            text=f"Yêu cầu bởi {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))