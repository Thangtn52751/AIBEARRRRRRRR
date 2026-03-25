import discord
from discord import app_commands
from discord.ext import commands


class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Xem danh sach lenh"
    )
    async def help_command(self, interaction: discord.Interaction) -> None:

        embed = discord.Embed(
            title="📚 TRUNG TÂM TRỢ GIÚP",
            description=(
                "✨ **Danh sách các lệnh của bot**\n"
                "👉 Gõ `/` để Discord gợi ý nhanh\n\n"
                "━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.blurple()
        )

        # ===== BASIC =====
        embed.add_field(
            name="⚙️ • LỆNH CƠ BẢN",
            value=(
                "➤ `/help` ┆ Xem danh sách lệnh\n"
                "➤ `/ping` ┆ Kiểm tra độ trễ"
            ),
            inline=False
        )

        # ===== USER =====
        embed.add_field(
            name="👤 • NGƯỜI DÙNG",
            value="➤ `/userinfo` ┆ Xem thông tin thành viên",
            inline=False
        )

        # ===== BIRTHDAY =====
        embed.add_field(
            name="🎂 • SINH NHẬT",
            value=(
                "➤ `/birthday set` ┆ Đặt ngày sinh\n"
                "➤ `/birthday clear` ┆ Xóa ngày sinh\n"
                "➤ `/birthday channel` ┆ Set kênh thông báo"
            ),
            inline=False
        )

        # ===== FUN =====
        embed.add_field(
            name="🎮 • GIẢI TRÍ",
            value="➤ `/roll` ┆ Tung xúc xắc (1-6)",
            inline=False
        )

        # ===== ADMIN =====
        embed.add_field(
            name="🛠️ • QUẢN TRỊ",
            value="➤ `/sync` ┆ Đồng bộ lệnh",
            inline=False
        )

        # ===== TIP =====
        embed.add_field(
            name="💡 MẸO",
            value="Dùng `/ + tên lệnh` để xem hướng dẫn chi tiết nhanh!",
            inline=False
        )

        # ===== FOOTER =====
        embed.set_footer(
            text=f"Yêu cầu bởi {interaction.user} • Béo Bot",
            icon_url=interaction.user.display_avatar.url
        )

        # ===== AVATAR BOT =====
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.display_avatar.url
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommand(bot))