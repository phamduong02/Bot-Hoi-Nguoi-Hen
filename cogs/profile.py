
from discord.ext import commands
import discord
from io import BytesIO
from pathlib import Path
from PIL import Image, UnidentifiedImageError
# Thêm get_weapons_of_char để kiểm tra đồ đang mặc
from core.database import get_profile, get_user, update_money, get_weapons_of_char
from core.profile_card import build_profile_card
from core.ui import WEAPON_ICON, get_icon
from core.combat_render_fast import get_emoji_text
from core.database import get_profile, get_user, update_money, get_team, get_character_by_id # Thêm team
BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_BG_CACHE = BASE_DIR / "data" / "profile_bg.png"
USER_PROFILE_BG_DIR = BASE_DIR / "data" / "profile_backgrounds"
PROFILE_BG_CHANNEL = "pc"
PROFILE_BG_CATEGORY = "data"


def _normalize_channel_name(name):
    return name.casefold().replace("-", "").replace("_", "").replace(" ", "")


def _find_profile_background_channel(guild):
    if guild is None:
        return None

    target_channel = _normalize_channel_name(PROFILE_BG_CHANNEL)
    target_category = _normalize_channel_name(PROFILE_BG_CATEGORY)

    for channel in guild.text_channels:
        category = channel.category
        if (
            _normalize_channel_name(channel.name) == target_channel
            and category is not None
            and _normalize_channel_name(category.name) == target_category
        ):
            return channel

    for channel in guild.text_channels:
        channel_name = _normalize_channel_name(channel.name)
        if channel_name in {target_channel, f"{target_category}{target_channel}"}:
            return channel

    return None


def _is_image_attachment(attachment):
    content_type = attachment.content_type or ""
    filename = attachment.filename.casefold()
    return content_type.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg", ".webp"))


def _user_profile_bg_path(user_id):
    return USER_PROFILE_BG_DIR / f"{user_id}.png"


def _save_profile_bg(user_id, image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGBA")
    except (UnidentifiedImageError, OSError):
        return None

    path = _user_profile_bg_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
    return path


async def _collect_profile_backgrounds_from_guild(guild, max_items=10):
    channel = _find_profile_background_channel(guild)
    if channel is None:
        return []

    backgrounds = []
    try:
        async for message in channel.history(limit=80):
            for attachment in message.attachments:
                if _is_image_attachment(attachment):
                    backgrounds.append((message, attachment))
                    if len(backgrounds) >= max_items:
                        return backgrounds
    except (discord.Forbidden, discord.HTTPException):
        return []

    return backgrounds


async def _collect_profile_backgrounds(ctx, max_items=10):
    return await _collect_profile_backgrounds_from_guild(ctx.guild, max_items)


async def refresh_profile_background_from_guild(guild):
    channel = _find_profile_background_channel(guild)
    if channel is None:
        return False

    try:
        async for message in channel.history(limit=50):
            for attachment in message.attachments:
                if not _is_image_attachment(attachment):
                    continue

                PROFILE_BG_CACHE.parent.mkdir(parents=True, exist_ok=True)
                PROFILE_BG_CACHE.write_bytes(await attachment.read())
                return True
    except (discord.Forbidden, discord.HTTPException, OSError):
        return False

    return False


async def refresh_profile_background(ctx):
    return await refresh_profile_background_from_guild(ctx.guild)


def _get_user_profile_bg(user_id):
    path = _user_profile_bg_path(user_id)
    return path if path.exists() else None

async def build_profile_card_message(member):
    user_id = str(member.id)
    user = get_user(user_id)
    profile = get_profile(user_id)
    
    # Lấy stats từ đội hình slot 1 để hiển thị trên thẻ
    team = get_team(user_id)
    char_stats = {"ATK": "0", "DEF": "0", "SPD": "0", "CRIT": "0%"}
    if team and team[1]:
        # Cần truyền user_id vào hàm get_character_by_id
        char = get_character_by_id(team[1], user_id)
        if char:
            char_stats = {
                "ATK": str(char[6]),
                "DEF": str(char[8]),
                "SPD": str(char[10]),
                "CRIT": f"{char[11]}%"
            }

    # Lấy nền riêng của người dùng
    bg_path = _get_user_profile_bg(user_id)
    bg_bytes = None
    if bg_path and bg_path.exists():
        bg_bytes = bg_path.read_bytes()

    # Truyền char_stats sang hàm build_profile_card
    card = await build_profile_card(member, user, profile, bg_bytes, char_stats)
    file = discord.File(card, filename="profile.png")
    embed = discord.Embed(color=0x66D9C4)
    embed.set_image(url="attachment://profile.png")
    return embed, file

class ProfileBackgroundSelect(discord.ui.Select):
    def __init__(self, backgrounds):
        options = []
        for index, (message, attachment) in enumerate(backgrounds, start=1):
            label = f"PC {index}"
            description = attachment.filename[:90]
            options.append(discord.SelectOption(label=label, value=str(index - 1), description=description))

        super().__init__(
            placeholder="Chọn ảnh nền profile card",
            min_values=1,
            max_values=1,
            options=options
        )
        self.backgrounds = backgrounds

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        _, attachment = self.backgrounds[index]

        try:
            path = _save_profile_bg(str(interaction.user.id), await attachment.read())
        except (discord.HTTPException, OSError):
            path = None

        if path is None:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Không thể lưu ảnh này.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"{get_icon('tick', interaction.guild, interaction.bot)} Đã chọn nền profile card riêng của bạn. Bấm `Làm mới` trên card để xem ảnh mới.",
            ephemeral=True
        )
        self.view.clear_items()
        self.view.stop()
        await interaction.message.edit(view=self.view)


class ProfileBackgroundView(discord.ui.View):
    def __init__(self, user_id, backgrounds):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(ProfileBackgroundSelect(backgrounds))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            return True

        await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Menu này không phải của bạn.", ephemeral=True)
        return False


class ProfileCardView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            return True

        await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Profile card này không phải của bạn.", ephemeral=True)
        return False

    @discord.ui.button(label="Đổi nền", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def change_background(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        backgrounds = await _collect_profile_backgrounds_from_guild(interaction.guild)

        if not backgrounds:
            await interaction.followup.send(
                f"{get_icon('cross', interaction.guild, interaction.bot)} Không tìm thấy ảnh trong kênh `data/pc` hoặc bot thiếu quyền đọc kênh đó.\n"
                "Bạn cũng có thể gửi ảnh kèm lệnh `hpc` để đặt trực tiếp.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🖼️ Chọn nền profile card",
            description="Chọn ảnh trong menu. Sau khi chọn xong, bấm `Làm mới` trên card.",
            color=0x66D9C4
        )
        embed.set_image(url=backgrounds[0][1].url)
        await interaction.followup.send(
            embed=embed,
            view=ProfileBackgroundView(interaction.user.id, backgrounds),
            ephemeral=True
        )

    @discord.ui.button(label="Làm mới", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_card(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if _get_user_profile_bg(str(interaction.user.id)) is None:
            await refresh_profile_background_from_guild(interaction.guild)

        embed, file = await build_profile_card_message(interaction.user)
        await interaction.message.edit(
            embed=embed,
            attachments=[file],
            view=ProfileCardView(interaction.user.id)
        )

    @discord.ui.button(label="Xóa nền", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def reset_background(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        path = _user_profile_bg_path(str(interaction.user.id))
        had_background = path.exists()

        if had_background:
            path.unlink()

        await refresh_profile_background_from_guild(interaction.guild)
        embed, file = await build_profile_card_message(interaction.user)
        await interaction.message.edit(
            embed=embed,
            attachments=[file],
            view=ProfileCardView(interaction.user.id)
        )

        if had_background:
            await interaction.followup.send(f"{get_icon('tick', interaction.guild, interaction.bot)} Đã xóa nền riêng và làm mới profile card.", ephemeral=True)
        else:
            await interaction.followup.send(f"{get_icon('cross', interaction.guild, interaction.bot)} Bạn chưa đặt nền riêng.", ephemeral=True)



class TransferConfirmView(discord.ui.View):
    def __init__(self, owner_id: int, sender_id: str, recipient_id: str, amount: int):
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount

    # === THÊM HÀM NÀY VÀO ĐỂ SỬA LỖI ===
    def disable_all_items(self):
        for item in self.children:
            item.disabled = True
    # ===================================

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Chỉ người gửi mới có thể xác nhận giao dịch này.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Có", style=discord.ButtonStyle.success, emoji=get_icon('tick', None, None))
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        sender = get_user(self.sender_id)
        if sender[1] < self.amount:
            await interaction.response.send_message(f"{get_icon('cross', interaction.guild, interaction.bot)} Bạn không còn đủ tiền để thực hiện giao dịch.", ephemeral=True)
            self.disable_all_items()
            await interaction.message.edit(view=self)
            return

        recipient = get_user(self.recipient_id)
        update_money(self.sender_id, sender[1] - self.amount)
        update_money(self.recipient_id, recipient[1] + self.amount)

        self.disable_all_items()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{get_emoji_text('money')} Chuyển tiền thành công",
                description=(
                    f"{interaction.user.mention} đã chuyển **{self.amount:,} {get_emoji_text('money')}** cho <@{self.recipient_id}>.\n"
                    f"Số dư hiện tại của bạn: **{sender[1] - self.amount:,} {get_emoji_text('money')}**"
                ),
                color=0x2ECC71
            ),
            view=self
        )

    @discord.ui.button(label="Không", style=discord.ButtonStyle.danger, emoji=get_icon('cross', None, None))
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.disable_all_items()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{get_icon('cross', interaction.guild, interaction.bot)} Giao dịch đã bị hủy",
                description="Bạn đã từ chối chuyển tiền.",
                color=0xE74C3C
            ),
            view=self
        )

class ProfileSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ĐỔI TÊN HÀM XỬ LÝ LỆNH ĐỂ CHẮC CHẮN KHÔNG TRÙNG
    @commands.command(name="hme", aliases=["profile", "me", "info"])
    async def hme_command(self, ctx):
        user_id = str(ctx.author.id)
        user = get_user(user_id)

        embed = discord.Embed(
            title=f"👤 HỒ SƠ: {ctx.author.display_name}",
            color=0x66D9C4
        )
        
        money_icon = get_emoji_text('money')
        embed.add_field(name="Tên người chơi", value=ctx.author.name, inline=True)
        embed.add_field(name="Tài sản", value=f"**{user[1]:,}** {money_icon}", inline=True)
        
        # Thêm thông tin level nếu có
        profile = get_profile(user_id)
        if profile:
            embed.add_field(name="Cấp độ", value=f"Level **{profile[1]}**", inline=True)

        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Gõ 'hpc' để xem Profile Card có ảnh nền xịn xò!")

        await ctx.send(embed=embed)

    @commands.command(name="pc", aliases=["setpc", "profilecard", "nenpc"])
    async def profile_card_background(self, ctx, action: str = None):
        # ... (Giữ nguyên logic xử lý ảnh nền từ cite 13) ...
        user_id = str(ctx.author.id)
        if action and action.casefold() in {"reset", "xoa", "xoá", "remove", "default"}:
            path = _user_profile_bg_path(user_id)
            if path.exists():
                path.unlink()
                await ctx.send(f"{get_icon('tick', ctx.guild, ctx.bot)} Đã xóa nền profile card riêng.")
            else:
                await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn chưa đặt nền profile card riêng.")
            await refresh_profile_background_from_guild(ctx.guild)
            embed, file = await build_profile_card_message(ctx.author)
            await ctx.send(embed=embed, file=file, view=ProfileCardView(ctx.author.id))
            return

        attachment = next((item for item in ctx.message.attachments if _is_image_attachment(item)), None)
        if attachment is not None:
            try:
                path = _save_profile_bg(user_id, await attachment.read())
            except (discord.HTTPException, OSError):
                path = None

            if path is None:
                await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Không thể lưu ảnh này.")
                return

            await ctx.send(f"{get_icon('tick', ctx.guild, ctx.bot)} Đã đặt ảnh bạn gửi làm nền profile card riêng.")
            embed, file = await build_profile_card_message(ctx.author)
            await ctx.send(embed=embed, file=file, view=ProfileCardView(ctx.author.id))
            return

        if _get_user_profile_bg(user_id) is None:
            await refresh_profile_background_from_guild(ctx.guild)

        embed, file = await build_profile_card_message(ctx.author)
        await ctx.send(embed=embed, file=file, view=ProfileCardView(ctx.author.id))

    @commands.command(name="hgive", aliases=["give", "chuyentien"])
    async def hgive(self, ctx, member: discord.Member = None, amount: int = 0):
        # ... (Giữ nguyên logic chuyển tiền từ cite 13) ...
        if member is None or amount <= 0:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Cú pháp: `hgive @nguoi_dung <số_tiền>`")
        if member.id == ctx.author.id:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Không thể tự chuyển cho mình!")
        
        sender_id = str(ctx.author.id)
        recipient_id = str(member.id)
        sender_data = get_user(sender_id)
        
        if not sender_data or sender_data[1] < amount:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn không đủ tiền!")

        view = TransferConfirmView(ctx.author.id, sender_id, recipient_id, amount)
        embed = discord.Embed(
            title=f"{get_emoji_text('money')} Xác nhận giao dịch",
            description=f"Chuyển **{amount:,} {get_emoji_text('money')}** cho {member.mention}?",
            color=0xFFCC00
        )
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    # ĐỔI Tên Cog ở đây luôn
    await bot.add_cog(ProfileSystem(bot))