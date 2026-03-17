import discord
from discord import app_commands
from discord.ext import commands


class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="userinfo",
        description="Xem thông tin của một thành viên."
    )
    @app_commands.describe(member="Thành viên bạn muốn xem thông tin")
    async def userinfo(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ) -> None:

        member = member or interaction.user

        joined_at = (
            member.joined_at.strftime("%d/%m/%Y %H:%M")
            if member.joined_at else "Không rõ"
        )

        created_at = member.created_at.strftime("%d/%m/%Y %H:%M")

        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_text = ", ".join(roles) if roles else "Không có role"

        embed = discord.Embed(
            title=f"👤 Thông tin người dùng",
            description=f"**{member.mention}**",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="📛 Username",
            value=f"{member}",
            inline=True
        )

        embed.add_field(
            name="🆔 User ID",
            value=member.id,
            inline=True
        )

        embed.add_field(
            name="📅 Tạo tài khoản",
            value=created_at,
            inline=False
        )

        embed.add_field(
            name="📥 Tham gia server",
            value=joined_at,
            inline=False
        )

        embed.add_field(
            name="⭐ Role cao nhất",
            value=member.top_role.mention,
            inline=True
        )

        embed.add_field(
            name="🎭 Số lượng role",
            value=len(roles),
            inline=True
        )

        embed.add_field(
            name="📜 Danh sách role",
            value=roles_text,
            inline=False
        )

        embed.set_footer(
            text=f"Yêu cầu bởi {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        embed.set_author(
            name=member,
            icon_url=member.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserInfo(bot))