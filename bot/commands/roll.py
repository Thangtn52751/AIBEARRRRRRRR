import random
import asyncio

import discord
from discord import app_commands
from discord.ext import commands


class Roll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="roll",
        description="Tung xúc xắc từ 1-6 🎲"
    )
    async def roll(self, interaction: discord.Interaction) -> None:

        # gửi trạng thái đang tung
        loading_embed = discord.Embed(
            title="🎲 Tung xúc xắc...",
            description="Đang lắc xúc xắc...",
            color=discord.Color.yellow()
        )

        await interaction.response.send_message(embed=loading_embed)

        # giả lập animation 2s
        await asyncio.sleep(2)

        dice = random.randint(1, 6)

        dice_emoji = {
            1: "⚀",
            2: "⚁",
            3: "⚂",
            4: "⚃",
            5: "⚄",
            6: "⚅"
        }

        result_embed = discord.Embed(
            title="🎲 Kết quả tung xúc xắc",
            description=f"{interaction.user.mention} đã tung được:",
            color=discord.Color.green()
        )

        result_embed.add_field(
            name="Kết quả",
            value=f"{dice_emoji[dice]} **{dice}**",
            inline=False
        )

        result_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        result_embed.set_footer(
            text="Chúc bạn may mắn lần sau 🍀"
        )

        await interaction.edit_original_response(embed=result_embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roll(bot))