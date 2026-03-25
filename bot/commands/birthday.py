import os
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.user_context import (
    load_guild_birthday_settings,
    save_guild_birthday_settings,
)


class Birthday(commands.Cog):
    birthday_group = app_commands.Group(
        name="birthday",
        description="Quản lý sinh nhật và kênh thông báo."
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_birthday_settings = load_guild_birthday_settings()
        self.timezone = self._load_timezone()

    async def cog_load(self) -> None:
        if not self.birthday_loop.is_running():
            self.birthday_loop.start()

    def cog_unload(self) -> None:
        if self.birthday_loop.is_running():
            self.birthday_loop.cancel()

    def _load_timezone(self) -> ZoneInfo:
        timezone_name = os.getenv("BIRTHDAY_TIMEZONE", "Asia/Bangkok")
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def _validate_birthday(self, day: int, month: int) -> date:
        try:
            return date(2000, month, day)
        except ValueError as error:
            raise ValueError("Ngày sinh không hợp lệ. Hãy nhập đúng ngày/tháng.") from error

    def _build_birthday_embed(
        self,
        member: discord.Member,
        guild: discord.Guild,
        today: date
    ) -> discord.Embed:
        embed = discord.Embed(
            title="Happy Birthday!",
            description=(
                f"Hôm nay là ngày sinh nhật {member.mention}.\n"
                "Chúc bạn có một sinh nhật thật nhiều niềm vui và may mắn!"
            ),
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Hôm nay",
            value=today.strftime("%d/%m"),
            inline=True
        )
        embed.add_field(
            name="Server",
            value=guild.name,
            inline=True
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Birthday system")
        return embed

    async def _resolve_member(
        self,
        guild: discord.Guild,
        user_id: int
    ) -> discord.Member | None:
        member = guild.get_member(user_id)
        if member is not None:
            return member

        try:
            return await guild.fetch_member(user_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    @birthday_group.command(
        name="set",
        description="Tự đặt ngày sinh của bạn."
    )
    @app_commands.describe(
        day="Ngày sinh của bạn",
        month="Tháng sinh của bạn"
    )
    async def set_birthday(
        self,
        interaction: discord.Interaction,
        day: app_commands.Range[int, 1, 31],
        month: app_commands.Range[int, 1, 12]
    ) -> None:
        try:
            birthday = self._validate_birthday(day, month)
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return

        self.bot.birthday_store.set_birthday(
            interaction.user.id,
            birthday.day,
            birthday.month
        )

        configured_channel = None
        if interaction.guild is not None:
            guild_setting = self.guild_birthday_settings.get(str(interaction.guild.id), {})
            channel_id = guild_setting.get("birthday_channel_id")
            if channel_id:
                try:
                    configured_channel = interaction.guild.get_channel(int(channel_id))
                except (TypeError, ValueError):
                    configured_channel = None

        message = f"Đã lưu ngày sinh của bạn: **{birthday.strftime('%d/%m')}**."
        if configured_channel is not None:
            message += f" Đến ngày đó mình sẽ thông báo tại: {configured_channel.mention}."
        elif interaction.guild is not None:
            message += " Server này chưa set kênh thông báo sinh nhật."

        await interaction.response.send_message(message, ephemeral=True)

    @birthday_group.command(
        name="channel",
        description="Chọn kênh để set."
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="Kênh nhận thông báo sinh nhật")
    async def set_birthday_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Lệnh này chỉ được dùng trong server.",
                ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Bạn cần quyền administrator để đặt kênh sinh nhật.",
                ephemeral=True
            )
            return

        if channel.guild.id != interaction.guild.id:
            await interaction.response.send_message(
                "Hãy chọn một kênh trong server này.",
                ephemeral=True
            )
            return

        bot_member = interaction.guild.me
        if bot_member is None:
            await interaction.response.send_message(
                "Không tìm thấy thông tin bot trong server để kiểm tra quyền.",
                ephemeral=True
            )
            return

        permissions = channel.permissions_for(bot_member)
        missing_permissions: list[str] = []
        if not permissions.send_messages:
            missing_permissions.append("Send Messages")
        if not permissions.embed_links:
            missing_permissions.append("Embed Links")
        if not permissions.mention_everyone:
            missing_permissions.append("Mention Everyone")

        if missing_permissions:
            await interaction.response.send_message(
                "Bot đang thiếu quyền trong kênh này: "
                + ", ".join(f"`{permission}`" for permission in missing_permissions),
                ephemeral=True
            )
            return

        guild_setting = self.guild_birthday_settings.setdefault(
            str(interaction.guild.id),
            {
                "birthday_channel_id": "",
                "last_announced": {}
            }
        )
        guild_setting["birthday_channel_id"] = str(channel.id)
        guild_setting.setdefault("last_announced", {})
        save_guild_birthday_settings(self.guild_birthday_settings)

        await interaction.response.send_message(
            f"Đã đặt kênh sinh nhật thành {channel.mention}.",
            ephemeral=True
        )

    @birthday_group.command(
        name="clear",
        description="Xóa ngày sinh nhật đã lưu của bạn."
    )
    async def clear_birthday(self, interaction: discord.Interaction) -> None:
        if self.bot.birthday_store.get_birthday(interaction.user.id) is None:
            await interaction.response.send_message(
                "Bạn chưa đặt ngày sinh.",
                ephemeral=True
            )
            return

        self.bot.birthday_store.delete_birthday(interaction.user.id)
        await interaction.response.send_message(
            "Đã xóa ngày sinh nhật của bạn.",
            ephemeral=True
        )

    @tasks.loop(minutes=30)
    async def birthday_loop(self) -> None:
        await self.bot.wait_until_ready()

        today = datetime.now(self.timezone).date()
        today_key = today.isoformat()
        settings_updated = False

        for guild_id, guild_setting in self.guild_birthday_settings.items():
            channel_id = guild_setting.get("birthday_channel_id")
            if not channel_id:
                continue

            try:
                guild = self.bot.get_guild(int(guild_id))
            except (TypeError, ValueError):
                continue

            if guild is None:
                continue

            try:
                channel = guild.get_channel(int(channel_id))
            except (TypeError, ValueError):
                continue

            if not isinstance(channel, discord.TextChannel):
                continue

            bot_member = guild.me
            if bot_member is None:
                continue

            permissions = channel.permissions_for(bot_member)
            if not (
                permissions.send_messages
                and permissions.embed_links
                and permissions.mention_everyone
            ):
                continue

            last_announced = guild_setting.setdefault("last_announced", {})

            for user_id in self.bot.birthday_store.get_users_by_birthday(today.day, today.month):
                if last_announced.get(user_id) == today_key:
                    continue

                try:
                    member = await self._resolve_member(guild, int(user_id))
                except (TypeError, ValueError):
                    continue

                if member is None:
                    continue

                embed = self._build_birthday_embed(member, guild, today)

                try:
                    await channel.send(
                        content=(
                            f"@everyone Hôm nay là ngày sinh nhật của {member.mention}. "
                            "🎂🎂🎂🎂 Happy Birthday!"
                        ),
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(
                            everyone=True,
                            users=True,
                            roles=False
                        )
                    )
                except discord.HTTPException:
                    continue

                last_announced[user_id] = today_key
                settings_updated = True

        if settings_updated:
            save_guild_birthday_settings(self.guild_birthday_settings)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Birthday(bot))
