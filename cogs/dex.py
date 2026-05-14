import discord
from discord.ext import commands

from core.database import get_characters, get_weapons_of_char
from core.game_data import CHARACTERS, MULTIPLIER, RARITY_ORDER
from core.weapon_data import WEAPONS
from core.ui import get_character_icon, get_rarity_icon, get_icon, CHARACTER_EMOJI_NAMES

# Thêm import skill nếu có, bỏ qua nếu chưa có
try:
    from core.skill_data import get_skill, get_skill_mana_cost
    _HAS_SKILL = True
except ImportError:
    _HAS_SKILL = False

# ── Bảng màu ──────────────────────────────────────────────────────────────────
RARITY_COLOR = {
    "Common":    0x95a5a6,
    "Uncommon":  0x2ecc71,
    "Rare":      0x3498db,
    "Epic":      0x9b59b6,
    "Mythic":    0xe74c3c,
    "Legendary": 0xe67e22,
    "Godlike":   0xffd700,
}

STAT_LABEL = {
    "hp":        "HP",
    "atk_phys":  "Tấn công",
    "atk_magic": "Phép thuật",
    "def_phys":  "Phòng thủ",
    "def_magic": "Kháng phép",
    "spd":       "Tốc độ",
    "crit":      "Chí mạng",
}

STAT_MAX = {
    "hp":        6000,
    "atk_phys":  2500,
    "atk_magic": 2000,
    "def_phys":  2000,
    "def_magic": 1500,
    "spd":       350,
    "crit":      100,
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _bar(val: int, max_val: int, length: int = 10) -> str:
    filled = round(min(val / max(1, max_val), 1.0) * length)
    return "█" * filled + "░" * (length - filled)


def _find_in_roster(query: str) -> dict | None:
    """
    Tìm tướng theo thứ tự ưu tiên:
    1. Khớp tên emoji chính xác  (hdex ahri  → emoji "ahri")
    2. Khớp tên tướng chính xác  (hdex Ahri)
    3. Khớp tên emoji một phần   (hdex ah)
    4. Khớp tên tướng một phần   (hdex ri)
    """
    q = query.casefold().strip()

    exact_emoji, partial_emoji = None, None
    exact_name,  partial_name  = None, None

    for char in CHARACTERS:
        name = char["name"]
        name_lower = name.casefold()
        emoji_names = CHARACTER_EMOJI_NAMES.get(name, ())

        if any(e.casefold() == q for e in emoji_names):
            if exact_emoji is None: exact_emoji = char

        if name_lower == q:
            if exact_name is None: exact_name = char

        if any(q in e.casefold() for e in emoji_names):
            if partial_emoji is None: partial_emoji = char

        if q in name_lower:
            if partial_name is None: partial_name = char

    return exact_emoji or exact_name or partial_emoji or partial_name


def _owned(all_chars: list, name: str) -> list:
    owned = [c for c in all_chars if c[2].casefold() == name.casefold()]
    def get_rarity_index(char_row):
        try:    return RARITY_ORDER.index(char_row[4])
        except: return -1
    owned.sort(key=get_rarity_index, reverse=True)
    return owned


# ── Build embed ───────────────────────────────────────────────────────────────
def _build_embed(ctx, roster_char, owned, guild, bot) -> discord.Embed:
    name  = roster_char["name"]
    count = len(owned)

    # NẾU CHƯA SỞ HỮU
    if count == 0:
        base_rarity = roster_char.get("rarity", "Common")
        base_cls    = roster_char.get("class", "Unknown")
        c_icon      = get_character_icon(name, base_cls, guild, bot)
        embed = discord.Embed(color=0x99aab5)
        embed.set_author(
            name=f"{name}  ·  {base_cls}  ·  {base_rarity}",
            icon_url=ctx.author.display_avatar.url,
        )
        embed.title = f"{c_icon}  {name}"
        embed.description = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
        embed.add_field(
            name="⚠️ Chưa sở hữu",
            value="Bạn chưa có tướng này.\nDùng `hcm` để thử vận may!",
            inline=False,
        )
        if _HAS_SKILL:
            skill = get_skill(name)
            if skill:
                cd = skill.get("cooldown")
                cd_text   = f" (CD {cd})" if cd is not None else ""
                mana_cost = get_skill_mana_cost(name)
                embed.add_field(
                    name="✨ Kỹ năng",
                    value=f"**{skill.get('name','Unknown')}**{cd_text} | Mana `{mana_cost}`\n{skill.get('description','')}".strip(),
                    inline=False,
                )
        return embed

    # NẾU ĐÃ SỞ HỮU (Lấy bản mạnh nhất)
    row           = owned[0]
    char_id       = row[0]
    actual_cls    = row[3]
    actual_rarity = row[4]
    
    stats = {
        "hp":        row[5],
        "atk_phys":  row[6],
        "atk_magic": row[7],
        "def_phys":  row[8],
        "def_magic": row[9],
        "spd":       row[10],
        "crit":      row[11],
    }

    # Tính toán chỉ số cộng thêm từ Vũ Khí
    weapons = get_weapons_of_char(char_id)
    bonus_stats = {"hp": 0, "atk_phys": 0, "atk_magic": 0, "def_phys": 0, "def_magic": 0, "spd": 0, "crit": 0}
    equipped_weapon_texts = []

    for w in weapons:
        # Dữ liệu w: 0:id, 1:code, 2..7: stat, 8:hp, 9:rarity, 10:rarity_roll
        bonus_stats["atk_phys"] += w[2]
        bonus_stats["atk_magic"] += w[3]
        bonus_stats["def_phys"] += w[4]
        bonus_stats["def_magic"] += w[5]
        bonus_stats["crit"] += w[6]
        bonus_stats["spd"] += w[7]
        bonus_stats["hp"] += int(w[8] or 0)
        
        w_data = WEAPONS.get(w[1], {})
        w_name = w_data.get("name", "Vũ khí bí ẩn")
        w_emoji = f":{w_data.get('emoji', '🗡️')}:"
        w_rarity = (w[9] if len(w) > 9 else None) or w_data.get("rarity", "Common")
        
        equipped_weapon_texts.append(f"{w_emoji} **{w_name}** `[{w_rarity}]` (ID: {w[0]})")

    c_icon = get_character_icon(name, actual_cls, guild, bot)
    r_icon = get_rarity_icon(actual_rarity, guild, bot)
    c_cls  = get_icon(actual_cls, guild, bot)

    embed = discord.Embed(color=RARITY_COLOR.get(actual_rarity, 0x99aab5))
    embed.set_author(
        name=f"Bản sao mạnh nhất: {actual_rarity}",
        icon_url=ctx.author.display_avatar.url,
    )
    embed.title = f"{c_icon}  {name} `(ID: #{char_id})`"
    embed.description = (
        f"{c_cls} **{actual_cls}** ·  {r_icon} **{actual_rarity}**\n"
        f"Bạn sở hữu: **{count} bản sao**\n"
        "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
    )

    hp_icon = get_icon("hp", guild, bot)
    base_hp = stats["hp"]
    bonus_hp = bonus_stats["hp"]
    total_hp = base_hp + bonus_hp
    hp_val = f"**{base_hp}** `(+{bonus_hp})`" if bonus_hp > 0 else f"**{base_hp}**"
    embed.add_field(
        name=f"{hp_icon} HP",
        value=f"`{_bar(total_hp, STAT_MAX['hp'], 20)}` {hp_val}",
        inline=False,
    )

    # Hàm vẽ cột chỉ số (Có hiển thị phần cộng thêm)
    def _col(keys):
        lines = []
        for k in keys:
            icon  = get_icon(k, guild, bot)
            label = STAT_LABEL[k]
            base_val   = stats[k]
            bonus_val  = bonus_stats[k]
            total_val  = base_val + bonus_val
            
            unit  = "%" if k == "crit" else ""
            bar   = _bar(total_val, STAT_MAX[k], 8)
            
            if bonus_val > 0:
                val_str = f"**{base_val}** `(+{bonus_val})`{unit}"
            else:
                val_str = f"**{base_val}**{unit}"
                
            lines.append(f"{icon} **{label}**\n`{bar}` {val_str}")
        return "\n\n".join(lines)

    embed.add_field(
        name="⚔️ Tấn công & Phòng thủ",
        value=_col(["atk_phys", "atk_magic", "def_phys"]),
        inline=True,
    )
    embed.add_field(
        name="🛡️ Kháng phép · Tốc · Crit",
        value=_col(["def_magic", "spd", "crit"]),
        inline=True,
    )

    # HIỂN THỊ VŨ KHÍ ĐANG TRANG BỊ
    if equipped_weapon_texts:
        embed.add_field(
            name="🗡️ Trang Bị Đang Mặc",
            value="\n".join(equipped_weapon_texts),
            inline=False
        )
    else:
        embed.add_field(
            name="🗡️ Trang Bị Đang Mặc",
            value="*Tay không (Dùng `hwp` để mặc đồ)*",
            inline=False
        )

    if _HAS_SKILL:
        skill = get_skill(name)
        if skill:
            cd = skill.get("cooldown")
            cd_text   = f" (CD {cd})" if cd is not None else ""
            mana_cost = get_skill_mana_cost(name)
            embed.add_field(
                name="✨ Kỹ năng",
                value=f"**{skill.get('name','Unknown')}**{cd_text} | Mana `{mana_cost}`\n{skill.get('description','')}".strip(),
                inline=False,
            )

    mult = MULTIPLIER.get(actual_rarity, 1.0)
    embed.add_field(
        name="📊 Hệ số chỉ số",
        value=f"**×{mult}** so với bản Common",
        inline=False,
    )

    if count > 1:
        ids    = " · ".join(f"`#{c[0]}`" for c in owned[:10])
        suffix = f" *(+{count-10} nữa)*" if count > 10 else ""
        embed.add_field(
            name=f"📋 ID Các bản sao ({count})",
            value=ids + suffix,
            inline=False,
        )

    embed.set_footer(text=f"HOIN RPG  ·  {name}  ·  {actual_cls}")
    return embed


# ── Cog ───────────────────────────────────────────────────────────────────────
class Dex(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="hdex", aliases=["dex", "xemtuong", "chitiet"])
    async def dex(self, ctx: commands.Context, *, query: str = None):
        if not query:
            embed = discord.Embed(
                title="📖 Cách dùng lệnh hdex",
                description=(
                    "```\nhdex <tên emoji tướng>\n```\n"
                    "**Ví dụ:**\n"
                    "`hdex ahri` → tìm tướng có emoji tên `ahri`\n"
                    "`hdex ez` → tìm tướng có emoji tên `ez`\n"
                    "`hdex daxua` → tìm Yasuo\n\n"
                    "Tìm theo tên emoji trong server. "
                    "Không phân biệt hoa thường, khớp một phần."
                ),
                color=0x3498db,
            )
            return await ctx.send(embed=embed)

        roster_char = _find_in_roster(query)
        if roster_char is None:
            return await ctx.send(
                f"❌ Không tìm thấy tướng với emoji **{query}**.\n"
                f"Dùng `hnhanvat` để xem danh sách tướng bạn có."
            )

        all_chars = get_characters(str(ctx.author.id))
        owned     = _owned(all_chars, roster_char["name"])
        embed     = _build_embed(ctx, roster_char, owned, ctx.guild, ctx.bot)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Dex(bot))
