import discord
from discord.ext import commands
from core.database import get_user, update_money, set_team
import json
from core.ui import get_icon
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

ADMIN_IDS: list[int] = config.get("admin_ids", [])


# ─── Views ────────────────────────────────────────────────────────────────────

class AdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in ADMIN_IDS:
            return True
        await interaction.response.send_message(
            f"{get_icon('cross', interaction.guild, interaction.client)} Bạn không có quyền dùng menu admin!", ephemeral=True
        )
        return False

    @discord.ui.button(label="💰 Cấp tiền",   style=discord.ButtonStyle.primary,   row=0)
    async def give_money(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(GiveMoneyModal())

    @discord.ui.button(label="🗑️ Xóa tiền",   style=discord.ButtonStyle.danger,    row=0)
    async def remove_money(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(RemoveMoneyModal())

    @discord.ui.button(label="🔄 Reset team", style=discord.ButtonStyle.secondary, row=0)
    async def reset_team(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(ResetTeamModal())

    @discord.ui.button(label="📢 Broadcast",  style=discord.ButtonStyle.success,   row=1)
    async def broadcast(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(BroadcastModal())

    @discord.ui.button(label="📊 Thống kê",   style=discord.ButtonStyle.primary,   row=1)
    async def stats(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        # Thống kê cơ bản từ DB
        try:
            import sqlite3
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            total_users    = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            total_chars    = c.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
            total_weapons  = c.execute("SELECT COUNT(*) FROM inventory_weapon").fetchone()[0]
            total_gold     = c.execute("SELECT SUM(money) FROM users").fetchone()[0] or 0
            registered     = c.execute("SELECT COUNT(*) FROM registered").fetchone()[0]
            conn.close()
            embed = discord.Embed(title="📊 Thống Kê Hệ Thống", color=0x2ecc71)
            embed.add_field(name="👤 Tài khoản",      value=f"**{total_users:,}**",   inline=True)
            embed.add_field(name=f"{get_icon('tick', interaction.guild, interaction.client)} Đã đăng ký",     value=f"**{registered:,}**",    inline=True)
            embed.add_field(name="🧝 Nhân vật",       value=f"**{total_chars:,}**",   inline=True)
            embed.add_field(name="⚔️ Vũ khí",         value=f"**{total_weapons:,}**", inline=True)
            embed.add_field(name="💰 Tổng Gold lưu thông", value=f"**{total_gold:,}**", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"{get_icon('cross', interaction.guild, interaction.client)} Lỗi thống kê: {e}", ephemeral=True)


# ─── Modals ───────────────────────────────────────────────────────────────────

class GiveMoneyModal(discord.ui.Modal, title="💰 Cấp tiền"):

    user_id = discord.ui.TextInput(
        label="User ID",
        placeholder="Discord ID của người chơi",
        max_length=20
    )

    amount = discord.ui.TextInput(
        label="Số tiền",
        placeholder="VD: 10000",
        max_length=12
    )

    async def on_submit(self, interaction: discord.Interaction):

        try:

            uid = self.user_id.value.strip()

            amt = int(
                self.amount.value
                .replace(",", "")
                .replace(".", "")
                .strip()
            )

            if amt <= 0:
                return await interaction.response.send_message(
                    f"{get_icon('cross', interaction.guild, interaction.client)} "
                    "Số tiền phải lớn hơn 0!",
                    ephemeral=True
                )

            user = get_user(uid)

            if not user:

                return await interaction.response.send_message(
                    f"{get_icon('cross', interaction.guild, interaction.client)} "
                    f"User `{uid}` chưa tham gia game!",
                    ephemeral=True
                )

            new_money = int(user[1]) + amt

            update_money(uid, new_money)

            await interaction.response.send_message(
                f"{get_icon('tick', interaction.guild, interaction.client)} "
                f"Đã cấp **{amt:,}** Gold cho <@{uid}>\n"
                f"Số dư mới: **{new_money:,}** Gold",
                ephemeral=True
            )

        except ValueError:

            await interaction.response.send_message(
                f"{get_icon('cross', interaction.guild, interaction.client)} "
                "Số tiền không hợp lệ!",
                ephemeral=True
            )

        except Exception as e:

            import traceback
            traceback.print_exc()

            await interaction.response.send_message(
                f"{get_icon('cross', interaction.guild, interaction.client)} "
                f"Lỗi: `{e}`",
                ephemeral=True
            )


class RemoveMoneyModal(discord.ui.Modal, title="🗑️ Xóa tiền"):
    user_id = discord.ui.TextInput(
        label="User ID", placeholder="Discord ID của người chơi", max_length=20
    )
    amount = discord.ui.TextInput(
        label="Số tiền cần xóa", placeholder="VD: 5000", max_length=12
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = self.user_id.value.strip()
            amt = int(self.amount.value.replace(",", "").replace(".", "").strip())
            if amt <= 0:
                return await interaction.response.send_message(
                    f"{get_icon('cross', interaction.guild, interaction.client)} Số tiền phải lớn hơn 0!", ephemeral=True)
            user = get_user(uid)

            if not user:

                return await interaction.response.send_message(
                    f"{get_icon('cross', interaction.guild, interaction.client)} "
                    f"User `{uid}` chưa tham gia game!",
                    ephemeral=True
                )

            new_money = max(0, int(user[1]) - amt)
            update_money(uid, new_money)
            await interaction.response.send_message(
                f"{get_icon('tick', interaction.guild, interaction.client)} Đã xóa **{amt:,}** Gold của <@{uid}>\n"
                f"Số dư mới: **{new_money:,}** Gold",
                ephemeral=True,
            )
        except ValueError:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.client)} Số tiền không hợp lệ!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.client)} Lỗi: {e}", ephemeral=True)


class ResetTeamModal(discord.ui.Modal, title="🔄 Reset team"):
    user_id = discord.ui.TextInput(
        label="User ID", placeholder="Discord ID của người chơi", max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = self.user_id.value.strip()
            get_user(uid)  # đảm bảo user tồn tại
            set_team(uid, None, None, None)
            await interaction.response.send_message(
                f"{get_icon('tick', interaction.guild, interaction.client)} Đã reset team của <@{uid}>", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.client)} Lỗi: {e}", ephemeral=True)


class BroadcastModal(discord.ui.Modal, title="📢 Broadcast"):
    message = discord.ui.TextInput(
        label="Nội dung thông báo",
        placeholder="Nhập nội dung...",
        style=discord.TextStyle.long,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="📢 Thông báo từ Ban Quản Trị",
                description=self.message.value,
                color=0xe74c3c,
            )
            embed.set_footer(text=f"Gửi bởi {interaction.user.display_name}")
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message(
                f"{get_icon('tick', interaction.guild, interaction.client)} Broadcast thành công!", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.client)} Lỗi: {e}", ephemeral=True)


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_admin(self, user_id: int) -> bool:
        return user_id in ADMIN_IDS

    @commands.command(name="admin")
    async def admin_panel(self, ctx: commands.Context):
        if not self.is_admin(ctx.author.id):
            await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn không có quyền admin!")
            return

        embed = discord.Embed(
            title="🛡️ Panel Admin — HoiNguoiHen RPG",
            description=(
                "Chọn chức năng bên dưới.\n"
                f"Admin hiện tại: **{len(ADMIN_IDS)}** người"
            ),
            color=0x2c3e50,
        )
        embed.set_footer(text=f"Thực hiện bởi {ctx.author.display_name}")
        await ctx.send(embed=embed, view=AdminView())


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))