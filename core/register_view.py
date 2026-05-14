
import discord
from discord.ext import commands
from core.register import is_registered, register_user
from core.ui import get_icon

# ── Nội dung điều khoản ───────────────────────────────────────────────────────
TERMS = """\
**1. Tài khoản**
Mỗi Discord account tương ứng 1 tài khoản game. Không chia sẻ, mua bán tài khoản.

**2. Fair Play**
Nghiêm cấm dùng bot, macro, hoặc bất kỳ công cụ tự động nào để farm tài nguyên.

**3. Nội dung**
Không dùng tên nhân vật, tên nhóm mang nội dung xúc phạm, phân biệt hay vi phạm pháp luật.

**4. Dữ liệu**
Dữ liệu game (nhân vật, vật phẩm, tiền tệ…) là tài sản ảo, không có giá trị quy đổi thực tế.

**5. Thay đổi điều khoản**
Ban quản trị có quyền thay đổi điều khoản bất kỳ lúc nào mà không cần thông báo trước.

**6. Xử phạt**
Vi phạm có thể dẫn đến khóa tài khoản vĩnh viễn mà không hoàn trả bất kỳ tài nguyên nào.
"""


# ── View xác nhận ─────────────────────────────────────────────────────────────
class RegisterView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                f"{get_icon('cross')} Đây không phải lời mời đăng ký của bạn.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label=f"{get_icon('tick')}  Tôi đồng ý & Tạo tài khoản",
        style=discord.ButtonStyle.success,
        custom_id="register_agree",
    )
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        register_user(str(interaction.user.id))

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="🎉 Đăng ký thành công!",
            description=(
                f"Chào mừng **{interaction.user.display_name}** đến với server!\n\n"
                "Tài khoản của bạn đã được tạo.\n"
                "Dùng lệnh **hcm** để bắt đầu nhận tướng đầu tiên nhé!"
            ),
            color=0x2ecc71,
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        self.stop()

    @discord.ui.button(
        label=f"{get_icon('cross')}  Từ chối",
        style=discord.ButtonStyle.danger,
        custom_id="register_decline",
    )
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="👋 Bạn đã từ chối. Dùng lại lệnh bất kỳ khi muốn đăng ký.",
            view=self,
            embed=None
        )

        self.stop()


# ── Hàm gửi embed điều khoản ──────────────────────────────────────────────────
async def send_register_prompt(ctx: commands.Context):
    embed = discord.Embed(
        title="📜 Điều khoản sử dụng",
        description=TERMS,
        color=0x3498db,
    )
    embed.set_footer(text="Bạn cần đồng ý điều khoản để bắt đầu chơi.")
    embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.display_avatar.url,
    )
    view = RegisterView(ctx.author.id)
    await ctx.send(embed=embed, view=view)


# ── Global bot check (thêm vào main.py) ───────────────────────────────────────
def setup_register_check(bot: commands.Bot):
    """
    Gọi hàm này trong main.py sau khi tạo bot:
        from core.register_view import setup_register_check
        setup_register_check(bot)
    """
    # Các lệnh không cần đăng ký
    EXEMPT = {"help"}

    @bot.check
    async def require_registration(ctx: commands.Context) -> bool:
        if ctx.command and ctx.command.qualified_name in EXEMPT:
            return True
        if is_registered(str(ctx.author.id)):
            return True
        # Chưa đăng ký → hiện prompt và chặn lệnh hiện tại
        await send_register_prompt(ctx)
        return False
