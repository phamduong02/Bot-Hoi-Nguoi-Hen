import discord
from discord.ext import commands
from core.database import get_weapons, get_characters, equip_weapon, unequip_weapon
from core.weapon_data import WEAPONS
from core.ui import get_weapon_icon, get_character_icon, get_icon
# =========================
# Dropdown chọn vũ khí
# =========================
class WeaponSelect(discord.ui.Select):
    def __init__(self, weapons, chars):
        # Tạo map ID -> Tên tướng để lấy tên hiển thị cho đẹp
        char_map = {c[0]: c[2] for c in chars}
        options = []

        # Sắp xếp: Ưu tiên Vũ khí chưa ai mặc (equipped_to == 0) lên trước, sau đó là ID mới nhất
        sorted_weapons = sorted(weapons, key=lambda w: (w[8] == 0, w[0]), reverse=True)

        for w in sorted_weapons[:25]:  # Discord giới hạn tối đa 25 options
            w_id = w[0]
            w_code = w[1]
            equipped_to = w[8]
            
            base_w = WEAPONS.get(w_code, {})
            name = base_w.get("name", "Vũ khí bí ẩn")
            
            # Cập nhật đủ cả MDEF và SPD
            stats = []
            if w[2] > 0: stats.append(f"ATK {w[2]}")
            if w[3] > 0: stats.append(f"MATK {w[3]}")
            if w[4] > 0: stats.append(f"DEF {w[4]}")
            if w[5] > 0: stats.append(f"MDEF {w[5]}")
            if w[6] > 0: stats.append(f"CRIT {w[6]}%")
            if w[7] > 0: stats.append(f"SPD {w[7]}")
            desc = " | ".join(stats)[:90] 

            label = f"{name} (ID: {w_id})"
            # Dùng Tên Tướng thay vì ID
            if equipped_to > 0:
                c_name = char_map.get(equipped_to, f"#{equipped_to}")
                label += f" [Đang mặc: {c_name}]"

            options.append(
                discord.SelectOption(
                    label=label[:100],
                    description=desc or "Không có chỉ số",
                    value=str(w_id)
                )
            )

        # Chống lỗi nếu không có option nào
        if not options:
            options.append(discord.SelectOption(label="Kho vũ khí trống", value="0"))

        super().__init__(placeholder="🗡️ Chọn vũ khí từ kho...", options=options)
        self.weapon_id = None

    async def callback(self, interaction: discord.Interaction):
        self.weapon_id = int(self.values[0])
        self.view.weapon_id = self.weapon_id
        await interaction.response.defer()


# =========================
# Dropdown chọn nhân vật
# =========================
class CharacterSelect(discord.ui.Select):
    def __init__(self, chars):
        options = []

        # Sắp xếp: Ưu tiên Tướng mới quay ra lên trước
        sorted_chars = sorted(chars, key=lambda c: c[0], reverse=True)

        for c in sorted_chars[:25]:
            options.append(
                discord.SelectOption(
                    label=f"{c[2]} (ID: {c[0]})",
                    description=f"Hệ: {c[3]} | Độ hiếm: {c[4]}",
                    value=str(c[0])
                )
            )

        if not options:
            options.append(discord.SelectOption(label="Không có tướng", value="0"))

        super().__init__(placeholder="👤 Chọn Tướng...", options=options)
        self.char_id = None

    async def callback(self, interaction: discord.Interaction):
        self.char_id = int(self.values[0])
        self.view.char_id = self.char_id
        await interaction.response.defer()


# =========================
# Button Trang bị
# =========================
class EquipButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="⚔️ Trang bị", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        user_id = str(interaction.user.id)

        if not view.weapon_id or not view.char_id:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Bạn phải chọn CẢ vũ khí VÀ nhân vật ở Menu phía trên!", ephemeral=True)
            return

        status = equip_weapon(user_id, view.char_id, view.weapon_id)

        if status == "success":
            await interaction.response.send_message(
                f"{get_icon('tick', interaction.guild, interaction.bot)} **Trang bị thành công!**\n🗡️ Vũ khí `#{view.weapon_id}` ➡️ 👤 Tướng `#{view.char_id}`",
                ephemeral=True
            )
            # F5 làm mới lại View ngay lập tức!
            await view.refresh_ui(interaction)
        elif status == "full":
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Tướng này đã cầm **tối đa 2 món đồ**! Hãy tháo bớt đồ cũ ra trước.", ephemeral=True)
        elif status == "already_equipped":
            await interaction.response.send_message("⚠️ Vũ khí này hiện đã được tướng này cầm sẵn rồi.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Lỗi: Bạn không sở hữu vũ khí này!", ephemeral=True)


# =========================
# Button tháo
# =========================
class UnequipButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🗑️ Tháo Vũ Khí", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        user_id = str(interaction.user.id)

        if not view.weapon_id:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Bạn cần chọn một vũ khí ở menu 1 để tiến hành tháo!", ephemeral=True)
            return

        success = unequip_weapon(user_id, view.weapon_id)

        if success:
            await interaction.response.send_message(f"{get_icon('tick', interaction.guild, interaction.bot)} Đã tháo vũ khí `#{view.weapon_id}` thành công và cất vào kho đồ!", ephemeral=True)
            # F5 làm mới lại View ngay lập tức!
            await view.refresh_ui(interaction)
        else:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Lỗi: Vũ khí không tồn tại, hoặc nó đang không được mặc.", ephemeral=True)


# =========================
# View chính
# =========================
class EquipView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.weapon_id = None
        self.char_id = None

        # Lấy lại dữ liệu mới nhất từ database mỗi khi View được tạo
        self.weapons = get_weapons(self.user_id)
        self.chars = get_characters(self.user_id)

        self.add_item(WeaponSelect(self.weapons, self.chars))
        self.add_item(CharacterSelect(self.chars))
        self.add_item(EquipButton())
        self.add_item(UnequipButton())

    async def refresh_ui(self, interaction: discord.Interaction):
        """Hàm thần thánh giúp cập nhật lại danh sách Dropdown lập tức"""
        new_view = EquipView(self.user_id)
        try:
            # Edit đè lên chính tin nhắn menu hiện tại
            await interaction.message.edit(view=new_view)
        except discord.HTTPException:
            pass


# =========================
# Command
# =========================
class EquipUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wp", aliases=["equip"])
    async def equip_menu(self, ctx):
        user_id = str(ctx.author.id)

        # Chỉ cần check xem kho có trống rỗng lúc gọi lệnh không
        if not get_weapons(user_id):
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Kho vũ khí của bạn đang trống! Dùng `hshop` để mua sắm.")

        if not get_characters(user_id):
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn chưa có tướng nào! Dùng `hcm` để chiêu mộ.")

        embed = discord.Embed(
            title="🛠️ XƯỞNG TRANG BỊ",
            description=(
                "1. Lựa chọn vũ khí bạn muốn thao tác từ Menu 1.\n"
                "2. Lựa chọn tướng từ Menu 2.\n"
                "3. Bấm **Trang bị** hoặc **Tháo Vũ Khí**.\n"
                "*(Lưu ý: Một tướng cầm tối đa 2 món đồ)*"
            ),
            color=0x5865F2
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        view = EquipView(user_id)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(EquipUI(bot))