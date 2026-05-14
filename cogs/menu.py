import discord
from discord.ext import commands

from core.gacha import summon_character
from core.database import get_user, update_money
from core.combat import fight_with_history
from core.ui import get_rarity_icon, get_character_icon, get_icon


class GameMenu(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot

    # ================= SUMMON =================

    @discord.ui.button(label="Quay", style=discord.ButtonStyle.primary, emoji="🎲")
    async def summon_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            user_id = str(interaction.user.id)

            user = get_user(user_id)
            if not user:
                return await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Bạn chưa có data!", ephemeral=True)

            money = user[1]

            if money < 300:
                return await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Không đủ tiền!", ephemeral=True)

            update_money(user_id, money - 300)

            result = summon_character(user_id)

            rarity_icon = get_rarity_icon(
                result.get("rarity", "common"),
                interaction.guild,
                self.bot
            )

            char_icon = get_character_icon(
                result.get("name"),
                result.get("class"),
                interaction.guild,
                self.bot
            )

            await interaction.response.send_message(
                f"🎉 Nhận được {rarity_icon} {char_icon} **{result['rarity']} {result['name']}**",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Error summon: {e}", ephemeral=True)

    # ================= HUNT =================

    @discord.ui.button(label="Săn quái", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def hunt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            user_id = str(interaction.user.id)

            result = fight_with_history(user_id)

            if result == "no_team":
                return await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Bạn chưa có team!", ephemeral=True)

            outcome, log, team, enemy, history = result

            log_text = "\n".join(log[:5]) if log else "No log"

            text = "🏆 WIN" if outcome == "win" else "💀 LOSE"

            await interaction.response.send_message(f"{text}\n{log_text}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Combat error: {e}", ephemeral=True)

    # ================= CHAR =================

    @discord.ui.button(label="Nhân vật", style=discord.ButtonStyle.secondary, emoji="📜")
    async def chars_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📜 Dùng `hnv` để xem danh sách nhân vật!",
            ephemeral=True
        )

    # ================= PROFILE =================

    @discord.ui.button(label="Hồ sơ", style=discord.ButtonStyle.success, emoji="👤")
    async def profile_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "👤 Dùng `hme` để xem hồ sơ!",
            ephemeral=True
        )


# ================= COG =================

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="menu")
    async def menu(self, ctx):

        embed = discord.Embed(
            title="🎮 GAME MENU",
            description="Chọn chức năng bên dưới:",
            color=0x00cec9
        )

        embed.add_field(name="🎲 Quay", value="Summon character", inline=False)
        embed.add_field(name="⚔️ Săn quái", value="Fight PvE", inline=False)
        embed.add_field(name="📜 Nhân vật", value="View characters", inline=False)
        embed.add_field(name="👤 Hồ sơ", value="Profile info", inline=False)

        view = GameMenu(self.bot)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Menu(bot))