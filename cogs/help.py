
from __future__ import annotations

from collections import Counter

import discord
from discord.ext import commands
from core.ui import get_icon
from core.ui import get_rarity_icon
# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

_SEP = "═" * 34


def _normalize_rates(rates: dict[str, float], default_key: str = "Common") -> dict[str, float]:
    dist = {k: max(0.0, float(v)) for k, v in (rates or {}).items()}
    total = sum(dist.values())
    if total <= 0:
        return {default_key: 1.0}

    if total < 1.0:
        dist[default_key] = dist.get(default_key, 0.0) + (1.0 - total)
        total = 1.0
    elif total > 1.0:
        for k in list(dist.keys()):
            dist[k] = dist[k] / total

    return dist


def _pct(rate: float) -> str:
    pct = float(rate) * 100.0
    if pct < 1:
        return f"{pct:.2f}%"
    if pct < 10:
        return f"{pct:.1f}%"
    return f"{pct:.0f}%"


def _lines(*items: str) -> str:
    return "\n".join([line for line in items if line])


def _gacha_rates_text(guild=None, bot=None) -> str:
    from core.game_data import RARITY, RARITY_ORDER

    dist = _normalize_rates(RARITY)

    lines = []

    for r in RARITY_ORDER:
        if r in dist:
            rarity_icon = get_rarity_icon(r, guild, bot)
            lines.append(f"{rarity_icon} **{r}** — {_pct(dist[r])}")

    return "\n".join(lines) or "—"


def _roster_counts_text() -> str:
    from core.game_data import CHARACTERS, RARITY_ORDER

    counts = Counter([c.get("rarity", "Common") for c in CHARACTERS])
    total = sum(counts.values())
    lines = []
    for r in RARITY_ORDER:
        if counts.get(r):
            lines.append(f"• **{r}**: {counts[r]}")
    lines.append(f"\nTổng: **{total} tướng**")
    return "\n".join(lines) if total else "—"


def _weapon_counts_text() -> str:
    from core.weapon_data import WEAPONS
    from core.game_data import RARITY_ORDER

    counts = Counter([w.get("rarity", "Common") for w in WEAPONS.values()])
    total = sum(counts.values())
    lines = []
    for r in RARITY_ORDER:
        if counts.get(r):
            lines.append(f"• **{r}**: {counts[r]}")
    lines.append(f"\nTổng: **{total} vũ khí**")
    return "\n".join(lines) if total else "—"


def _weapon_chest_rates_text(guild=None, bot=None) -> str:
    from core.weapon_data import WEAPON_RARITY_RATES
    from core.game_data import RARITY_ORDER

    dist = _normalize_rates(WEAPON_RARITY_RATES)

    lines = []

    for r in RARITY_ORDER:
        if r in dist:
            rarity_icon = get_rarity_icon(r, guild, bot)
            lines.append(f"{rarity_icon} **{r}** — {_pct(dist[r])}")

    return "\n".join(lines) or "—"


# ══════════════════════════════════════════════════════════════════════════════
# Sections metadata
# ══════════════════════════════════════════════════════════════════════════════

SECTION_META: dict[str, dict[str, object]] = {
    "home": {
        "label": "🏠 Trang chủ",
        "color": 0x2B2D31,
        "title": "📖  Bảng Lệnh · HoiNguoiHen",
        "desc": (
            "Tiền tố lệnh: **`h`** hoặc **`H`**\n"
            "Chọn danh mục bên dưới để xem chi tiết."
        ),
        "footer": "HoiNguoiHen RPG Bot  ·  Dùng nút bên dưới để xem chi tiết",
    },
    "profile": {
        "label": "👤 Hồ sơ",
        "color": 0x66D9C4,
        "title": "👤  Hồ sơ cá nhân",
        "desc": "Quản lý thông tin, profile card và số dư tài khoản.",
        "footer": "Tip: Dùng hpc để có card đẹp hơn hme",
    },
    "gacha": {
        "label": "🎲 Gacha",
        "color": 0x9B59B6,
        "title": "🎲  Chiêu mộ tướng",
        "desc": "Triệu hồi tướng mới bằng hệ thống gacha.",
        "footer": "Tip: Tướng hiếm có chỉ số mạnh hơn",
    },
    "combat": {
        "label": "⚔️ Chiến đấu",
        "color": 0xE74C3C,
        "title": "⚔️  Chiến đấu",
        "desc": "Đưa team vào trận để kiếm Gold, EXP và vũ khí.",
        "footer": "Tip: Nhớ trang bị vũ khí trước khi đi săn",
    },
    "inventory": {
        "label": "🎒 Kho đồ",
        "color": 0xF39C12,
        "title": "🎒  Kho vũ khí & trang bị",
        "desc": "Quản lý vũ khí và trang bị cho tướng.",
        "footer": "Tip: Mỗi tướng cầm tối đa 2 vũ khí",
    },
    "team": {
        "label": "👥 Đội hình",
        "color": 0x3498DB,
        "title": "👥  Nhân vật & đội hình",
        "desc": "Xem tướng bạn sở hữu và set team để chiến đấu.",
        "footer": "Tip: Kết hợp Tank + DPS + Mage để cân bằng",
    },
    "economy": {
        "label": "💰 Kinh tế",
        "color": 0x2ECC71,
        "title": "💰  Kinh tế & cửa hàng",
        "desc": "Kiếm và tiêu Gold trong game.",
        "footer": "Tip: Streak điểm danh giúp farm Gold rất nhanh",
    },
    "daily": {
        "label": "🗓️ Hằng ngày",
        "color": 0xF1C40F,
        "title": "🗓️  Điểm danh hằng ngày",
        "desc": "Nhận thưởng mỗi ngày và xây dựng streak để nhận bonus.",
        "footer": "Tip: Streak 7+ có rơi vũ khí mỗi ngày!",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Embed builder
# ══════════════════════════════════════════════════════════════════════════════

def _build_fields(
    section: str,
    guild=None,
    bot=None
) -> list[tuple[str, str, bool]]:
    if section == "home":
        return [
            (
                "🚀 Bắt đầu nhanh",
                _lines(
                    "`hhelp` → Mở bảng lệnh",
                    "`hmenu` → Menu nhanh",
                    "`hdaily` → Điểm danh nhận quà",
                    "`hcm` → Chiêu mộ tướng (x1/x10)",
                    "`hnv` → Xem tướng đang có",
                    "`hchontuong` → Set đội hình",
                    "`hb` → Đi săn (PvE) / `hb @user` (PvP)",
                    "`hshop` → Shop vũ khí theo ngày",
                    "`hmua 1 xN` → Mua rương vũ khí · `hmoruong xN` → Mở rương",
                    "`hvk` → Xem kho vũ khí · `hwp` → Trang bị vũ khí",
                    "`htaixiu` → Tài xỉu (casino)",
                ),
                False,
            ),
            ("📊 Thống kê nhanh", _lines(_roster_counts_text(), "", _weapon_counts_text()), False),
        ]

    if section == "profile":
        return [
            (
                "📌 Lệnh",
                _lines(
                    "`hme`  ·  `hprofile`  ·  `hinfo`",
                    "→ Xem nhanh hồ sơ + số dư",
                    "",
                    "`hpc`  ·  `hnenpc`",
                    "→ Profile card (có nút đổi/xóa ảnh nền)",
                    "",
                    "`hpc reset`",
                    "→ Xóa nền profile card riêng, về mặc định",
                ),
                False,
            ),
            (
                "🖼️ Đổi ảnh nền",
                _lines(
                    "• Gửi ảnh kèm lệnh `hpc`",
                    "• Hoặc bấm nút **Đổi nền** trên card → chọn trong menu",
                    "Hỗ trợ: `.png` `.jpg` `.jpeg` `.webp`",
                ),
                False,
            ),
        ]

    if section == "gacha":
        return [
            (
                "📌 Lệnh",
                _lines(
                    "`hcm`  ·  `hchieumo`  ·  `hsummon`",
                    "→ Chiêu mộ 1 lần (500 Gold)",
                    "",
                    "`hcm 10`  ·  `hcm x10`",
                    "→ Chiêu mộ 10 lần (5,000 Gold) (chỉ hỗ trợ 1 hoặc 10)",
                ),
                False,
            ),
            ("💎 Tỷ lệ độ hiếm", _gacha_rates_text(guild, bot), False),
            ("📊 Tướng trong roster", _roster_counts_text(), False),
        ]

    if section == "combat":
        return [
            (
                "📌 PvE / PvP",
                _lines(
                    "`hb`  ·  `hfight`  ·  `hcombat`",
                    "→ PvE săn quái ngẫu nhiên",
                    "",
                    "`hb @user`",
                    "→ PvP (đối phương cần bấm **Xác nhận**)",
                ),
                False,
            ),
            (
                "🎁 Thưởng (khi thắng PvE)",
                _lines(
                    "• 💰 +200 Gold",
                    "• ⭐ +50 EXP",
                    "• 🎁 10% rơi vũ khí",
                ),
                False,
            ),
            ("⏳ Cooldown", "PvE: **10 giây** giữa các trận", True),
            ("⚠️ Yêu cầu", "Phải set team trước bằng `hchontuong`", True),
        ]

    if section == "inventory":
        return [
            (
                "📌 Lệnh",
                _lines(
                    "`hvk`  ·  `hvukhi`  ·  `hkho`",
                    "→ Xem toàn bộ vũ khí trong kho",
                    "",
                    "`hwp`  ·  `hequip`",
                    "→ Mở giao diện trang bị/tháo vũ khí cho tướng",
                ),
                False,
            ),
            (
                "🧩 Cơ chế vũ khí",
                _lines(
                    "• Mỗi vũ khí có **stat** + **passive** riêng",
                    "• Mỗi tướng cầm tối đa **2 vũ khí**",
                    "• Có `rarity_roll` dạng `%` khi roll (càng cao càng hiếm)",
                    "• Passive được kích hoạt tự động trong combat",
                ),
                False,
            ),
            (
                "🎁 Nhận vũ khí",
                _lines(
                    "• Mua trong shop: `hshop`",
                    "• Mua/mở rương: `hmua 1 xN` → `hmoruong xN`",
                    "• Rơi khi thắng PvE: `hb` (10%)",
                    "• Rơi khi điểm danh (mốc streak): `hdaily`",
                ),
                False,
            ),
            ("🗡️ Danh sách vũ khí", _weapon_counts_text(), False),
        ]

    if section == "team":
        return [
            (
                "📌 Lệnh",
                _lines(
                    "`hnv`  ·  `hnhanvat`",
                    "→ Xem danh sách tướng bạn sở hữu (theo nhóm)",
                    "",
                    "`hdex <emoji/tên>`",
                    "→ Xem chi tiết tướng + vũ khí đang mặc",
                    "",
                    "`hchontuong`",
                    "→ Mở menu chọn team (dropdown)",
                    "",
                    "`hchontuong <id1> [id2] [id3]`",
                    "→ Set team nhanh bằng ID nhóm (VD: `hchontuong 1 3 5`)",
                    "",
                    "`hmyteam`",
                    "→ Xem team hiện tại",
                ),
                False,
            ),
            (
                "📋 ID nhóm tướng",
                _lines(
                    "Dùng `hnv` để xem danh sách và ID nhóm.",
                    "Nhóm = tất cả bản sao cùng tên tướng.",
                ),
                False,
            ),
        ]

    if section == "economy":
        return [
            (
                "🏪 Shop & rương vũ khí",
                _lines(
                    "`hshop`",
                    "→ Shop vũ khí theo ngày (mua bằng dropdown)",
                    "",
                    "`hmua 1 xN`",
                    "→ Mua rương vũ khí (item id `1`)",
                    "",
                    "`hmoruong xN`",
                    "→ Mở rương vũ khí (tối đa 10/lần)",
                ),
                False,
            ),
            ("🎁 Tỷ lệ rương vũ khí", _weapon_chest_rates_text(guild, bot), False),
            (
                "💸 Chuyển tiền",
                _lines(
                    "`hgive @user <số_tiền>`  ·  `hchuyentien`",
                    "→ Chuyển Gold cho người chơi khác (có xác nhận)",
                    "Lưu ý: không thể chuyển cho chính mình hoặc số âm.",
                ),
                False,
            ),
            (
                "🎰 Casino",
                _lines(
                    "`htaixiu`  ·  `htx`  ·  `hcasino`",
                    "→ Mở phiên Tài Xỉu trong kênh (làm theo nút trong phiên)",
                    "Giới hạn cược tối đa hiện tại: `500,000` Gold",
                ),
                False,
            ),
        ]

    if section == "daily":
        return [
            (
                "📌 Lệnh",
                _lines(
                    "`hdaily`  ·  `hdiemdanh`",
                    "→ Nhận thưởng điểm danh hôm nay",
                    "Reset lúc **00:00 giờ Việt Nam** (UTC+7)",
                ),
                False,
            ),
            (
                "🎁 Phần thưởng",
                _lines(
                    "💰 **Gold:** Random **500–2,000** mỗi ngày",
                    "⭐ **EXP:** Random **10–30** + bonus streak",
                    "",
                    "**Streak milestones:**",
                    "• Ngày 3: **+300** Gold + 30% rơi vũ khí",
                    "• Ngày 5: **+500** Gold + 50% rơi vũ khí",
                    "• Ngày 7+: **+1,000** Gold + 100% vũ khí 🔥",
                ),
                False,
            ),
            (
                "🔥 Streak",
                _lines(
                    f"{get_icon('tick', guild, bot)} Điểm danh liên tiếp → streak tăng",
                    f"{get_icon('cross', guild, bot)} Bỏ ≥ 2 ngày → streak reset về 1",
                    f"{get_icon('tick', guild, bot)} Streak 7+ duy trì nhận thưởng ngày 7 mỗi ngày",
                ),
                False,
            ),
        ]

    return []


def build_help_embed(
    section: str = "home",
    guild=None,
    bot=None
) -> discord.Embed:
    meta = SECTION_META.get(section, SECTION_META["home"])
    embed = discord.Embed(
        title=str(meta["title"]),
        description=f"{meta['desc']}\n{_SEP}",
        color=int(meta["color"]),
    )

    for name, value, inline in _build_fields(section, guild, bot):
        embed.add_field(name=name, value=value, inline=inline)

    embed.set_footer(text=str(meta.get("footer", "HOIN RPG Bot")))
    return embed


# ══════════════════════════════════════════════════════════════════════════════
# View (buttons)
# ══════════════════════════════════
_BUTTONS = [
    ("home", discord.ButtonStyle.secondary, 0),
    ("profile", discord.ButtonStyle.primary, 0),
    ("gacha", discord.ButtonStyle.primary, 0),
    ("combat", discord.ButtonStyle.danger, 0),
    ("inventory", discord.ButtonStyle.primary, 1),
    ("team", discord.ButtonStyle.primary, 1),
    ("economy", discord.ButtonStyle.success, 1),
    ("daily", discord.ButtonStyle.success, 1),
]


class HelpView(discord.ui.View):
    def __init__(self, bot, current: str = "home"):
        super().__init__(timeout=180)

        self.bot = bot
        self.current = current

        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for key, style, row in _BUTTONS:
            data = SECTION_META[key]
            is_current = key == self.current

            btn_style = discord.ButtonStyle.secondary if is_current else style
            btn = discord.ui.Button(
                label=str(data["label"]),
                style=btn_style,
                row=row,
                disabled=is_current,
                custom_id=f"help_{key}",
            )
            btn.callback = self._make_callback(key)
            self.add_item(btn)

    def _make_callback(self, key: str):
        async def callback(interaction: discord.Interaction):
            self.current = key
            self._build_buttons()
            await interaction.response.edit_message(embed=build_help_embed(key, guild=interaction.guild, bot=self.bot), view=self)

        return callback


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["hhelp", "commands"])
    async def help_command(self, ctx):
        await ctx.send(embed=build_help_embed("home", guild=ctx.guild, bot=self.bot) , view=HelpView(self.bot, "home"))


async def setup(bot):
    await bot.add_cog(Help(bot))
