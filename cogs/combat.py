import discord
from discord.ext import commands
import io
import random
import traceback

from core.combat import fight_with_history, fight_pvp_with_history
from core.database import get_user, update_money, add_exp, add_weapon
from core.cooldown import check_cooldown
from core.ui import get_weapon_icon, get_character_icon, get_character_avatar, get_icon
from core.weapon_data import generate_weapon_instance
from core.combat_render_fast import render_combat_battle, inject_bot 


# ── HÀM TẠO VŨ KHÍ RỚT KHI ĐÁNH THẮNG ──
def _generate_random_weapon():
    return generate_weapon_instance()


# ================= VIEW PVP =================
class PvPConfirmView(discord.ui.View):
    def __init__(self, challenger_id, challenger_name, defender_id, bot):
        super().__init__(timeout=60)
        self.challenger_id = challenger_id
        self.challenger_name = challenger_name
        self.defender_id = defender_id
        self.bot = bot

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.defender_id:
            await interaction.response.send_message(
                f"{get_icon('cross', interaction.guild, interaction.bot)} Chỉ người bị thách đấu mới được bấm nút này.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Chấp Nhận", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        result = fight_pvp_with_history(
            str(self.challenger_id),
            str(self.defender_id),
            self.bot
        )

        if not result:
            return await interaction.followup.send(f"{get_icon('cross', interaction.guild, interaction.bot)} Trận đấu PvP gặp lỗi.")

        outcome, log, p1, p2, history = result

        if outcome == "error":
            return await interaction.followup.send(f"{get_icon('cross', interaction.guild, interaction.bot)} Một trong hai chưa thiết lập đội hình!")

        try:
            frames, durations = render_combat_battle(
                history=history, 
                player_name=self.challenger_name, 
                enemy_name=interaction.user.name, 
                outcome=outcome,
                is_pvp=True
            )

            buffer = io.BytesIO()
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0
            )
            buffer.seek(0)

            file = discord.File(buffer, filename="summary.gif")

            embed = discord.Embed(
                title=f"⚔️ PvP: {self.challenger_name} vs {interaction.user.name}",
                color=0x00ff99 if outcome == "p1_win" else 0xff5555
            )

            embed.set_image(url="attachment://summary.gif")

            winner = self.challenger_name if outcome == "p1_win" else interaction.user.name
            embed.add_field(name="🏆 Người Chiến Thắng", value=winner, inline=False)

            self.disable_all()
            await interaction.message.edit(view=self)

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            traceback.print_exc()
            await interaction.followup.send(f"{get_icon('cross', interaction.guild, interaction.bot)} Lỗi xuất ảnh GIF: {e}")

    @discord.ui.button(label="Từ Chối", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.disable_all()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{get_icon('cross', interaction.guild, interaction.bot)} Đã từ chối",
                description=f"{interaction.user.mention} đã từ chối lời khiêu chiến.",
                color=0xff0000
            ),
            view=self
        )


# ================= MAIN COG =================
class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        inject_bot(bot) 

    # ================= PVE =================
    @commands.command(name="hb", aliases=["fight", "combat", "b"])
    async def hunt(self, ctx, member: discord.Member = None):
        user_id = str(ctx.author.id)

        # ===== PvP REQUEST =====
        if member:
            if member.id == ctx.author.id:
                return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Đừng tự đánh chính mình chứ!")

            if not get_user(user_id) or not get_user(str(member.id)):
                return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Dữ liệu người chơi không tồn tại!")

            embed = discord.Embed(
                title="⚔️ Thách Đấu PvP",
                description=f"{ctx.author.mention} muốn so tài với {member.mention}",
                color=0xffcc00
            )

            view = PvPConfirmView(ctx.author.id, ctx.author.name, member.id, self.bot)
            return await ctx.send(embed=embed, view=view)

        # ===== COOLDOWN =====
        ok, left = check_cooldown(user_id, "hunt", 10)
        if not ok:
            return await ctx.send(f"⏳ Đợi đã! Thể lực sẽ hồi sau {left}s")

        msg = await ctx.send("⏳ Đang múa kiếm đợi xíu nhé...")

        # ===== PVE =====
        result = fight_with_history(user_id, self.bot)

        if result == "no_team":
            return await msg.edit(content=f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn chưa gắn tướng vào đội hình!")

        outcome, log, team, monster, history = result

        try:
            frames, durations = render_combat_battle(
                history=history, 
                player_name=ctx.author.name, 
                enemy_name="Quái Vật", 
                outcome=outcome,
                is_pvp=False
            )

            buffer = io.BytesIO()
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0
            )
            buffer.seek(0)

            file = discord.File(buffer, filename="summary.gif")

            embed = discord.Embed(
                title=f"⚔️ Báo cáo chiến đấu: {ctx.author.name}",
                color=0x00ff99 if outcome == "win" else 0xff5555
            )

            embed.set_image(url="attachment://summary.gif")

            # ===== REWARD (VỚI HỆ THỐNG VŨ KHÍ MỚI) =====
            if outcome == "win":
                user = get_user(user_id)

                update_money(user_id, user[1] + 200)
                add_exp(user_id, 50)

                reward = f"{get_icon('gold', ctx.guild, ctx.bot)} +200 Gold | {get_icon('exp', ctx.guild, ctx.bot)} +50 EXP"

                # Tỷ lệ 10% rớt vũ khí khi săn quái thành công
                if random.random() < 0.10: 
                    w = _generate_random_weapon()
                    st = dict(w["stats"])
                    st["rarity"] = w.get("rarity")
                    st["rarity_roll"] = w.get("rarity_roll", 0)
                    add_weapon(user_id, w["code"], st)

                    w_emoji = get_weapon_icon(w.get("emoji", ""), ctx.guild, self.bot)
                    stat_str = " | ".join([f"{k.upper()}: {v}" for k, v in w["stats"].items()]) or "—"
                    reward += (
                        f"\n\n🎁 **Rơi Trang Bị:** [**{w.get('rarity','Common')}**] (roll `{w.get('rarity_roll',0)}%`) "
                        f"{w_emoji} **{w.get('name','Weapon')}**\n"
                        f"└ 📊 `{stat_str}`\n"
                        f"└ ✨ {w.get('passive_text','')}"
                    )

                embed.add_field(name="🏆 Phần thưởng", value=reward, inline=False)
            else:
                embed.add_field(name="💀 Kết quả", value="Đội hình của bạn đã bị tiêu diệt.", inline=False)

            await msg.edit(content=None, embed=embed, attachments=[file])

        except Exception as e:
            traceback.print_exc()
            await msg.edit(content=f"{get_icon('cross', ctx.guild, ctx.bot)} Render error: {e}")

async def setup(bot):
    await bot.add_cog(Combat(bot))
