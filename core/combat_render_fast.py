from urllib.request import urlopen, Request
from urllib.error import URLError
from io import BytesIO
import textwrap, re, threading, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import discord
import random
from core.ui import (
    get_icon,
    get_weapon_icon
)
# ─── Config ───────────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"

def _load_guild_id(key: str, default: int = 0) -> int:
    try:
        with _CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        guilds = cfg.get("emoji_guilds", {})
        return int(guilds.get(key, default) or default)
    except Exception:
        return default

STAT_GUILD_ID = _load_guild_id("stats", 1500158247435501628)

# ─── Background image ─────────────────────────────────────────────────────────
# ─── Background image ─────────────────────────────────────────────────────────

BACKGROUND_CHANNEL_ID = 1503204976636461238

_BG_URLS = []

_BG_LOCAL = Path(__file__).resolve().parents[1] / "icon" / "battle.jpg"


def _get_background() -> "Image.Image | None":

    # =========================================================
    # LOCAL BACKGROUND
    # =========================================================

    if _BG_LOCAL.exists():

        try:

            bg = Image.open(_BG_LOCAL).convert("RGBA")

            bg = bg.resize(
                (WIDTH, HEIGHT),
                Image.LANCZOS
            )

            return bg

        except Exception as e:

            print(f"{get_icon('cross')} Lỗi nền local:", e)

    # =========================================================
    # DISCORD BACKGROUND
    # =========================================================

    try:

        if not _BG_URLS:

            print(f"{get_icon('cross')} Không có background Discord")

            return None

        bg_url = random.choice(_BG_URLS)

        print(f"🖼️ Load background: {bg_url}")

        req = Request(
            bg_url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urlopen(req, timeout=8) as r:

            bg = Image.open(
                BytesIO(r.read())
            ).convert("RGBA")

        bg = bg.resize(
            (WIDTH, HEIGHT),
            Image.LANCZOS
        )

        return bg

    except Exception as e:

        print(f"{get_icon('cross')} Lỗi load background Discord:", e)

        return None
# ─── Kích thước ĐÃ ĐƯỢC MỞ RỘNG ────────────────────────────────────────────────
WIDTH       = 1500
HEIGHT      = 1350  # Kéo dài xuống để nhét vừa 3 con quái vật mà không bị lỗi
CARD_W      = 480
CARD_H      = 350
AVATAR_SIZE = 120

# ─── Màu ──────────────────────────────────────────────────────────────────────
BG_COLOR    = (5,  8,  28)
PLAYER_CARD = (20, 32, 80)
ENEMY_CARD  = (80, 16, 24)
HP_BG       = (40, 40, 50)
HP_GREEN    = (50, 200, 90)
HP_YELLOW   = (220, 180, 30)
HP_RED      = (210, 50,  50)
MANA_BG     = (25, 45, 90)
MANA_FILL   = (70, 150, 255)
GOLD        = (255, 210, 80)
WHITE       = (255, 255, 255)
GREY        = (180, 180, 200)

# ─── Font ─────────────────────────────────────────────────────────────────────
def _try_font(name, size):
    for p in [f"C:/Windows/Fonts/{name}",
              f"/usr/share/fonts/truetype/dejavu/{name}",
              f"/usr/share/fonts/truetype/liberation/{name}"]:
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default()

FONT_TITLE  = _try_font("arialbd.ttf", 52)
FONT_NAME   = _try_font("arialbd.ttf", 28)
FONT_BAR    = _try_font("arialbd.ttf", 17)  
FONT_MANA   = _try_font("arialbd.ttf", 14)  
FONT_STAT   = _try_font("arial.ttf",   22)
FONT_LOG    = _try_font("arial.ttf",   22)
FONT_VS     = _try_font("arialbd.ttf", 64)

# ─── Image fetch ──────────────────────────────────────────────────────────────
_IMG_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()
_EMOJI_RE = re.compile(r"<(a?):(\w+):(\d+)>")

def _fetch_url(url: str, size: tuple, circle: bool) -> Image.Image | None:
    cache_key = (url, size, circle)
    with _CACHE_LOCK:
        if cache_key in _IMG_CACHE:
            return _IMG_CACHE[cache_key]
    result = None
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urlopen(req, timeout=5) as r:
            raw = Image.open(BytesIO(r.read())).convert("RGBA")
        
        # ── Downsample 2 bước: giữ nét khi thu nhỏ nhiều ──
        src_w, src_h = raw.size
        target_w, target_h = size
        # Bước 1: nếu ảnh gốc lớn hơn 2x target → thu về 2x trước
        if src_w > target_w * 2 or src_h > target_h * 2:
            mid_w = max(target_w * 2, target_w)
            mid_h = max(target_h * 2, target_h)
            raw = raw.resize((mid_w, mid_h), Image.LANCZOS)
        # Bước 2: resize về kích thước cuối
        raw = raw.resize(size, Image.LANCZOS)
        
        if circle:
            mask = Image.new("L", size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size[0]-1, size[1]-1), fill=255)
            raw.putalpha(mask)
        result = raw
    except Exception as e:
        print(f"{get_icon('cross')} Lỗi load ảnh/emoji: {e}")
        result = None
    with _CACHE_LOCK:
        _IMG_CACHE[cache_key] = result
    return result

def _emoji_url(emoji_str: str) -> str | None:
    if not isinstance(emoji_str, str): return None
    m = _EMOJI_RE.match(emoji_str.strip())
    if m: return f"https://cdn.discordapp.com/emojis/{m.group(3)}.png?size=128"
    return None

_BOT_REF = None
_STAT_EMOJI_NAMES = {
    "atk_phys":  "hnh_atk",
    "atk_magic": "hnh_matk",
    "def_phys":  "hnh_def",
    "def_magic": "hnh_mdef",
    "spd":       "hnh_spd",
    "crit":      "hnh_crit",
    "hp":        "hnh_hp",
    "money":     "hnh_coin",
}

def inject_bot(bot):
    global _BOT_REF
    _BOT_REF = bot
    _IMG_CACHE.clear()

async def load_backgrounds_from_channel():

    global _BG_URLS

    if _BOT_REF is None:

        print(f"{get_icon('cross')} BOT REF NONE")

        return

    channel = _BOT_REF.get_channel(
        BACKGROUND_CHANNEL_ID
    )

    if not channel:

        print(f"{get_icon('cross')} Không tìm thấy channel background")

        return

    urls = []

    async for msg in channel.history(limit=100):

        for att in msg.attachments:

            try:

                if (
                    att.content_type
                    and "image" in att.content_type
                ):

                    urls.append(att.url)

            except:
                pass

    _BG_URLS = urls

    print(
        f"{get_icon('tick')} Loaded {len(_BG_URLS)} background images"
    )

def _get_stat_icon(key: str, size=(36, 36)) -> Image.Image | None:
    if _BOT_REF is None: return None
    emoji_name = _STAT_EMOJI_NAMES.get(key, "")
    guild = _BOT_REF.get_guild(STAT_GUILD_ID)
    emojis = guild.emojis if guild else _BOT_REF.emojis
    for e in emojis:
        if e.name.lower() == emoji_name.lower():
            url = f"https://cdn.discordapp.com/emojis/{e.id}.png?size=256"
            return _fetch_url(url, size, circle=False)
    return None

def _get_avatar_icon(
    emoji_str: str,
    size=(AVATAR_SIZE, AVATAR_SIZE)
) -> Image.Image | None:

    if not emoji_str:
        return None

    emoji_str = str(emoji_str)

    # Nếu là URL trực tiếp
    if emoji_str.startswith("http"):
        return _fetch_url(
            emoji_str,
            size,
            circle=False
        )

    # Nếu là custom emoji Discord
    match = re.search(
        r"<a?:\w+:(\d+)>",
        emoji_str
    )

    if match:

        emoji_id = match.group(1)

        url = (
            f"https://cdn.discordapp.com/"
            f"emojis/{emoji_id}.png?size=256"
        )

        return _fetch_url(
            url,
            size,
            circle=False
        )

    return None

def _draw_bar_with_text(draw, x, y, w, h, current, maximum, bg_color, fill_color_fn, font, text: str):
    maximum = max(1, maximum)
    current = max(0, current)
    ratio   = min(1.0, current / maximum)
    fill_w  = max(0, int(w * ratio))
    draw.rounded_rectangle((x, y, x+w, y+h), radius=h//2, fill=bg_color)
    if fill_w > 0:
        col = fill_color_fn(ratio)
        draw.rounded_rectangle((x, y, x+fill_w, y+h), radius=h//2, fill=col)
        draw.line([(x+6, y+3), (x+fill_w-6, y+3)], fill=(255, 255, 255, 60), width=1)
    draw.rounded_rectangle((x, y, x+w, y+h), radius=h//2, outline=(255, 255, 255, 40), width=1)
    if text:
        bb = draw.textbbox((0, 0), text, font=font)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        tx, ty = x + (w - tw) // 2, y + (h - th) // 2
        draw.text((tx+1, ty+1), text, font=font, fill=(0, 0, 0, 160))
        draw.text((tx, ty), text, font=font, fill=WHITE)

def _hp_color(ratio):
    if ratio > 0.5: return HP_GREEN
    if ratio > 0.25: return HP_YELLOW
    return HP_RED

def _mana_color(_): return MANA_FILL

def _draw_stat(base, draw, x, y, key, label, val, color):
    icon = _get_stat_icon(key)
    if icon:
        base.paste(icon, (x, y - 6), icon)
        draw.text((x + 42, y), str(val), fill=color, font=FONT_STAT)
    else:
        draw.text((x, y), f"{label}:{val}", fill=color, font=FONT_STAT)
# ─── Card Settings ────────────────────────────────────────────────────────────
HP_BAR_H   = 26
MANA_BAR_H = 20
ICON_SZ    = 36

def _draw_card(base: Image.Image, draw: ImageDraw.ImageDraw, x, y, char: dict, is_enemy: bool):
    card_color = (*ENEMY_CARD, 210) if is_enemy else (*PLAYER_CARD, 210)
    card_layer = Image.new("RGBA", (CARD_W, CARD_H), (0,0,0,0))
    card_draw  = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle((0, 0, CARD_W, CARD_H), radius=18, fill=card_color, outline=(255,255,255,45), width=1)
    base.alpha_composite(card_layer, dest=(x, y))

    avatar_url = char.get("avatar", "")
    av_img = None
    if avatar_url:
        av_img = _fetch_url(
            avatar_url,
            (AVATAR_SIZE * 2, AVATAR_SIZE * 2),  # fetch 2x
            circle=False
        )
        if av_img:
            av_img = av_img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)  # downsample về size thật
    av_x, av_y = x+14, y+14
    if av_img:
        draw.ellipse((av_x-2, av_y-2, av_x+AVATAR_SIZE+2, av_y+AVATAR_SIZE+2), fill=(255,255,255,20))
        base.paste(av_img, (av_x, av_y), av_img)
    else:
        draw.rounded_rectangle((av_x, av_y, av_x+AVATAR_SIZE, av_y+AVATAR_SIZE), radius=12, fill=(40, 40, 60))

    ix, iy = av_x + AVATAR_SIZE + 16, y + 14
    name = str(char.get("name", "Unknown"))
    draw.text((ix, iy), name, fill=WHITE, font=FONT_NAME)

    rarity = char.get("rarity", "")
    if rarity:
        rc = {"Common": (120,120,130), "Uncommon": (50,180,100), "Rare": (60,120,240), "Epic": (150,60,220), "Mythic": (220,50,50), "Legendary": (220,130,30), "Godlike": (200,160,0), "Monster": (180,60,60)}.get(rarity, (100,100,120))
        bb = draw.textbbox((0,0), rarity, font=FONT_LOG)
        rw = bb[2]-bb[0]+16
        draw.rounded_rectangle((ix, iy+34, ix+rw, iy+56), radius=8, fill=rc+(180,))
        draw.text((ix+8, iy+35), rarity, fill=WHITE, font=FONT_LOG)

    hp, max_hp = max(0, char.get("hp", 0)), max(1, char.get("max_hp", 1))
    bar_x, bar_y, bar_w = ix, iy + 64, CARD_W - AVATAR_SIZE - 46
    _draw_bar_with_text(draw, bar_x, bar_y, bar_w, HP_BAR_H, hp, max_hp, HP_BG, _hp_color, FONT_BAR, f"HP  {hp} / {max_hp}")

    mana_max, next_y = char.get("mana_max", 0), bar_y + HP_BAR_H + 6
    if mana_max:
        mana = max(0, char.get("mana", 0))
        _draw_bar_with_text(draw, bar_x, next_y, bar_w, MANA_BAR_H, mana, mana_max, MANA_BG, _mana_color, FONT_MANA, f"Mana  {mana} / {mana_max}")
        next_y += MANA_BAR_H + 8

    stat_y1, stat_y2 = next_y + 4, next_y + 4 + ICON_SZ + 10
    col_w, cols = (CARD_W - AVATAR_SIZE - 46) // 3, [bar_x, bar_x + (CARD_W - AVATAR_SIZE - 46) // 3, bar_x + ((CARD_W - AVATAR_SIZE - 46) // 3)*2]

    for ci, (key, lbl, val, col) in enumerate([("atk_phys", "ATK", char.get("atk_phys", 0), "#FFD54F"), ("def_phys", "DEF", char.get("def_phys", 0), "#4DA3FF"), ("spd", "SPD", char.get("spd", 0), "#FFFFFF")]):
        _draw_stat(base, draw, cols[ci], stat_y1, key, lbl, val, col)
    for ci, (key, lbl, val, col) in enumerate([("atk_magic", "MATK", char.get("atk_magic", 0), "#FF99CC"), ("def_magic", "MDEF", char.get("def_magic", 0), "#99CCFF"), ("crit", "CRT", f"{char.get('crit',0)}%", "#FF5B5B")]):
        _draw_stat(base, draw, cols[ci], stat_y2, key, lbl, val, col)

# ─── Weapon Icons ─────────────────────────────
    weapon_y = stat_y2 + ICON_SZ + 15
    weapon_x = bar_x

    weapons = char.get("equipped_weapons", [])

    # Lọc: chỉ giữ custom Discord emoji <:name:id> — bỏ hết Unicode/ô vuông
# ─── Weapon Icons ─────────────────────────────
    if weapons:

        # vị trí
        weapon_y = stat_y2 + ICON_SZ + 22

        # size mới
        WEAPON_SIZE = 84
        GAP = 20

        # chỉ hiện tối đa 2 món
        weapons = weapons[:2]

        for i, weapon_code in enumerate(weapons):

            if not weapon_code:
                continue

            weapon_code = str(weapon_code).strip()

            # lấy emoji discord
            emoji_text = get_weapon_icon(
                weapon_code,
                bot=_BOT_REF
            )

            # convert thành image
            weapon_icon = _get_avatar_icon(
                emoji_text,
                size=(WEAPON_SIZE, WEAPON_SIZE)
            )

            if weapon_icon:

                # vị trí từng ô
                wx = bar_x + (i * (WEAPON_SIZE + GAP))

                # nền ô
                draw.rounded_rectangle(
                    (
                        wx - 4,
                        weapon_y - 4,
                        wx + WEAPON_SIZE + 4,
                        weapon_y + WEAPON_SIZE + 4
                    ),
                    radius=10,
                    fill=(255,255,255,18),
                    outline=(255,255,255,35),
                    width=1
                )

                # paste icon
                base.paste(
                    weapon_icon,
                    (wx, weapon_y),
                    weapon_icon
                )
    if hp <= 0:
        ov = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=18, fill=(0,0,0,160))
        base.alpha_composite(ov.convert("RGBA"), dest=(x, y))
        draw = ImageDraw.Draw(base)
        fn_dead = _try_font("arialbd.ttf", 32)
        bb = draw.textbbox((0,0), "ĐÃ BẠI", fn_dead)
        draw.text((x+(CARD_W-(bb[2]-bb[0]))//2, y+(CARD_H-(bb[3]-bb[1]))//2), "ĐÃ BẠI", font=fn_dead, fill=(255,70,70))

def _draw_title(draw, outcome, is_final):
    text, color = ("CHIẾN THẮNG!" if outcome in ("win","p1_win") else "THẤT BẠI", (80,255,120) if outcome in ("win","p1_win") else (255,80,80)) if is_final else ("ĐANG CHIẾN ĐẤU", GOLD)
    bb = draw.textbbox((0,0), text, font=FONT_TITLE)
    draw.text(((WIDTH-(bb[2]-bb[0]))//2, 28), text, fill=color, font=FONT_TITLE)

def render_combat_battle(history: list, player_name: str, enemy_name: str, outcome: str, rewards: dict = None, is_pvp: bool = False) -> tuple:
    if not history: raise ValueError("history must not be empty")
    total = len(history)
    frames_to_render = list(range(total)) if total <= 5 else [0, total // 4, total // 2, (total * 3) // 4, total - 1]
    rendered, durations = [], []

    for fi, idx in enumerate(frames_to_render):
        frame, is_final = history[idx], (fi == len(frames_to_render)-1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR+(255,))
        bg = _get_background()
        if bg is not None:
            img.paste(bg, (0, 0))
            img.alpha_composite(Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 155)))
        else:
            draw_tmp = ImageDraw.Draw(img)
            for gy2 in range(HEIGHT):
                t = gy2 / HEIGHT
                draw_tmp.line([(0, gy2), (WIDTH, gy2)], fill=(int(5+18*t), int(8+12*t), int(28+35*t), 255))
        
        draw = ImageDraw.Draw(img)
        _draw_title(draw, outcome, is_final)
        draw.text((60, 90), player_name, fill=(150,200,255), font=FONT_LOG)
        bb2 = draw.textbbox((0,0), enemy_name, font=FONT_LOG)
        draw.text((WIDTH-bb2[2]+bb2[0]-60, 90), enemy_name, fill=(255,150,150), font=FONT_LOG)
        bb_vs = draw.textbbox((0,0), "VS", font=FONT_VS)
        draw.text(((WIDTH-(bb_vs[2]-bb_vs[0]))//2, HEIGHT//2 - 60), "VS", fill=GOLD, font=FONT_VS)

        player_team, enemy_team = frame.get("player", [])[:3], frame.get("enemy", [])[:3]
        card_start_y, gap = 115, 14

        for i, char in enumerate(player_team):
            _draw_card(img, ImageDraw.Draw(img), 30, card_start_y + i*(CARD_H+gap), char, False)
        for i, char in enumerate(enemy_team):
            _draw_card(img, ImageDraw.Draw(img), WIDTH-CARD_W-30, card_start_y + i*(CARD_H+gap), char, True)

        if is_final and rewards:
            rw_txt = "  ·  ".join(f"+{v} {k.upper()}" for k,v in rewards.items())
            bb_r = ImageDraw.Draw(img).textbbox((0,0), rw_txt, font=FONT_LOG)
            ImageDraw.Draw(img).text(((WIDTH-(bb_r[2]-bb_r[0]))//2, 78), rw_txt, fill=GOLD, font=FONT_LOG)

        rendered.append(img.convert("RGB"))
        durations.append(3000 if is_final else 1500)
    return rendered, durations

def get_emoji_text(key: str) -> str:
    if _BOT_REF is None: return get_icon('gold') 
    emoji_name = _STAT_EMOJI_NAMES.get(key, "")
    guild = _BOT_REF.get_guild(STAT_GUILD_ID)
    emojis = guild.emojis if guild else _BOT_REF.emojis
    for e in emojis:
        if e.name.lower() == emoji_name.lower(): return str(e) 
    return get_icon('gold') 

def render_summary_battle(history, outcome, stat_urls=None, player_name="Người chơi", enemy_name="Kẻ thù"):
    return render_combat_battle(history, player_name, enemy_name, outcome)