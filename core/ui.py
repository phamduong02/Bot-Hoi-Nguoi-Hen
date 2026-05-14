import json
from pathlib import Path

from core.game_data import CHARACTERS
import re

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    config = json.load(f)

EMOJI_GUILDS = config.get("emoji_guilds", {})

DICE_GUILD_ID = int(EMOJI_GUILDS.get("dice", 0))
CHARACTER_GUILD_ID = int(EMOJI_GUILDS.get("character", 0))
UI_GUILD_ID = int(EMOJI_GUILDS.get("ui", 0))
STAT_GUILD_ID = int(EMOJI_GUILDS.get("stats", 0))

# THÊM WEAPON GUILD ID VÀO ĐÂY ĐỂ ĐỌC TỪ CONFIG.JSON
WEAPON_GUILD_ID = int(EMOJI_GUILDS.get("weapon", 0))


# ═══════════════════════════════════════════════
# FALLBACK ICONS
# ═══════════════════════════════════════════════

ICON_FALLBACKS = {
    # rarity
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "mythic": "🔴",
    "legendary": "🟠", 
    "godlike": "👑",   

    # class
    "tank": "🛡️",
    "mage": "🔮",
    "warrior": "⚔️",
    "assassin": "🗡️",
    "adc": "🏹",       

    # stats
    "hp": "❤️",
    "atk_phys": "⚔️",
    "atk_magic": "🔮",
    "def_phys": "🛡️",
    "def_magic": "🧿",
    "spd": "⚡",
    "crit": "💥",

    # economy
    "tick": "✅",
    "cross": "❌",
    "exp": "⭐",
    "gold": "💰",
}

# ═══════════════════════════════════════════════
# CUSTOM EMOJI NAMES
# ═══════════════════════════════════════════════

ICON_NAMES = {
    # rarity
    "common": ("hnh_common",),
    "uncommon": ("hnh_uncommon",),
    "rare": ("hnh_rare",),
    "epic": ("hnh_epic",),
    "mythic": ("hnh_mythic",),
    "legendary": ("hnh_legendary",), 
    "godlike": ("hnh_godlike",),     

    # class
    "tank": ("hnh_tanker",),
    "mage": ("hnh_mage",),
    "warrior": ("hnh_warrior",),
    "assassin": ("hnh_assassin",),
    "adc": ("hnh_adc",),             
    
    # stats
    "hp": ("hnh_hp",),
    "atk_phys": ("hnh_atk",),
    "atk_magic": ("hnh_matk",),
    "def_phys": ("hnh_def",),
    "def_magic": ("hnh_mdef",),
    "spd": ("hnh_spd",),
    "crit": ("hnh_crit",),

    # economy
    "gold": ("hnh_coin",),
    "exp": ("hnh_exp",),

    # misc
    "weapon": ("hnh_weapon",),
    "team": ("hnh_team",),
    "inventory": ("hnh_inventory",),
    "daily": ("hnh_daily",),
    "combat": ("hnh_combat",),
    "tick": ("tick", "hnh_tick"),
    "cross": ("cross", "hnh_cross"),
}


# ═══════════════════════════════════════════════
# CHARACTER EMOJI NAMES
# ═══════════════════════════════════════════════

def _unique(values):
    result = []

    for value in values:
        if value and value not in result:
            result.append(value)

    return tuple(result)


def _normalize(text: str):
    return (
        str(text)
        .lower()
        .replace(" ", "")
        .replace("'", "")
        .replace(".", "")
        .replace("&", "")
    )


CHARACTER_EMOJI_NAMES = {}

for character in CHARACTERS:

    emoji_name = character.get("emoji")
    aliases    = list(character.get("emoji_aliases", ()))

    # CHỈ dùng tên emoji thực để lookup — không thêm tên tiếng Việt
    lookup_names = [emoji_name] + aliases

    CHARACTER_EMOJI_NAMES[character["name"]] = _unique(
        _normalize(a)
        for a in lookup_names
        if a
    )
# ═══════════════════════════════════════════════
# GUILD ITERATOR
# ═══════════════════════════════════════════════

def _iter_lookup_guilds(guild=None, bot=None, preferred_guild_id=None):
    seen = set()

    if bot and preferred_guild_id:
        preferred = bot.get_guild(preferred_guild_id)
        if preferred:
            seen.add(preferred.id)
            yield preferred

    if guild and guild.id not in seen:
        seen.add(guild.id)
        yield guild


# ═══════════════════════════════════════════════
# FIND EMOJI
# ═══════════════════════════════════════════════

def _find_custom_emoji(emoji_names, guilds):
    wanted = {
        _normalize(name)
        for name in emoji_names
        if name
    }

    for guild in guilds:
        for emoji in getattr(guild, "emojis", []):
            if _normalize(emoji.name) in wanted:
                return str(emoji)

    return None


# ═══════════════════════════════════════════════
# MAIN ICON SYSTEM
# ═══════════════════════════════════════════════

def get_icon(
    name,
    guild=None,
    bot=None,
    guild_id=None
):
    key = str(name).lower()

    emoji = _find_custom_emoji(
        ICON_NAMES.get(key, ()),
        _iter_lookup_guilds(
            guild,
            bot,
            guild_id or STAT_GUILD_ID
        ),
    )

    if emoji:
        return emoji

    return ICON_FALLBACKS.get(key, "•")


# ═══════════════════════════════════════════════
# CHARACTER ICON
# ═══════════════════════════════════════════════

def get_character_icon(
    character_name,
    cls=None,
    guild=None,
    bot=None
):
    emoji_names = CHARACTER_EMOJI_NAMES.get(character_name, ())

    emoji = _find_custom_emoji(
        emoji_names,
        _iter_lookup_guilds(
            guild,
            bot,
            CHARACTER_GUILD_ID,
        ),
    )

    if emoji:
        return emoji

    if cls:
        return get_icon(
            cls,
            guild=guild,
            bot=bot,
            guild_id=UI_GUILD_ID,
        )

    return "👤"


# ═══════════════════════════════════════════════
# RARITY ICON
# ═══════════════════════════════════════════════

def get_rarity_icon(
    rarity,
    guild=None,
    bot=None
):
    return get_icon(
        rarity,
        guild=guild,
        bot=bot,
        guild_id=UI_GUILD_ID
    )


# ═══════════════════════════════════════════════
# STAT ICONS
# ═══════════════════════════════════════════════

STAT_ICON = {
    "hp": "hp",
    "atk_phys": "atk_phys",
    "atk_magic": "atk_magic",
    "def_phys": "def_phys",
    "def_magic": "def_magic",
    "spd": "spd",
    "crit": "crit",
}


# ═══════════════════════════════════════════════
# WEAPON ICONS
# ═══════════════════════════════════════════════

WEAPON_ICON = {
    "phys": "⚔️",
    "magic": "🔮",
    "crit": "💥",
}


def get_weapon_icon(emoji_name, guild=None, bot=None):
    """
    Tìm emoji vũ khí từ Server Vũ Khí (WEAPON_GUILD_ID).
    Tự động hỗ trợ cả tên gốc lẫn tên có chứa tiền tố 'hnh_'
    """
    if not emoji_name:
        return "🗡️"

    # Mở rộng phạm vi tìm kiếm để quét được cả emoji của bạn
    emoji_names = (emoji_name, f"hnh_{emoji_name}")

    emoji = _find_custom_emoji(
        emoji_names,
        _iter_lookup_guilds(
            guild,
            bot,
            WEAPON_GUILD_ID,
        ),
    )

    if emoji:
        return emoji

    # Trả về text dạng :tên: nếu rủi ro không load được ảnh
    return f":{emoji_name}:"


EMOJI_REGEX = re.compile(r"<(a?):(\w+):(\d+)>")

def emoji_to_url(emoji_string):
    if not emoji_string:
        return None

    match = EMOJI_REGEX.match(str(emoji_string))

    if not match:
        return None

    animated, name, emoji_id = match.groups()
    ext = "gif" if animated else "png"

    return f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size=128&quality=lossless"


# ═══════════════════════════════════════════════
# CHARACTER AVATAR URL
# ═══════════════════════════════════════════════

def get_character_avatar(
    character_name,
    cls=None,
    guild=None,
    bot=None
):
    emoji = get_character_icon(
        character_name,
        cls,
        guild,
        bot
    )

    return emoji_to_url(emoji)


# ═══════════════════════════════════════════════
# STAT AVATAR URL
# ═══════════════════════════════════════════════

def get_stat_icon_url(
    stat_name,
    guild=None,
    bot=None
):
    emoji = get_icon(
        stat_name,
        guild,
        bot,
        guild_id=STAT_GUILD_ID
    )
    return emoji_to_url(emoji)
