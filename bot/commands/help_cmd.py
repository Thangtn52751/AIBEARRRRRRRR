import discord
from discord import app_commands
from discord.ext import commands


class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Xem danh sách lệnh"
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="📚 Trung tâm trợ giúp",
            description=(
                "Chào mừng đến với **bảng lệnh của bot**.\n"
                "Dưới đây là các lệnh bạn có thể sử dụng."
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📖 Lệnh cơ bản",
            value=(
                "`/help` - Xem danh sách tất cả lệnh của bot.\n"
                "`/ping` - Kiểm tra độ trễ hiện tại của bot."
            ),
            inline=False
        )

        embed.add_field(
            name="👤 Thông tin người dùng",
            value="`/userinfo` - Xem thông tin cơ bản của một thành viên.",
            inline=False
        )

        embed.add_field(
            name="🎲 Giải trí",
            value="`/roll` - Tung xúc xắc ngẫu nhiên từ **1 → 6**.",
            inline=False
        )

        embed.add_field(
            name="⚙️ Quản trị bot",
            value="`/sync` - Đồng bộ lại slash command trong server.",
            inline=False
        )

        embed.set_footer(
            text=f"Yêu cầu bởi {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.display_avatar.url
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommand(bot))