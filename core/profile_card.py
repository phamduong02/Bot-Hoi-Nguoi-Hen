from io import BytesIO
from pathlib import Path
import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE_DIR = Path(__file__).resolve().parents[1]
CARD_SIZE = (1000, 600)  # Thu gọn chiều cao vì đã bỏ mục tiền

def _font(size, bold=False):
    font_names = ("seguisb.ttf", "segoeuib.ttf") if bold else ("segoeui.ttf", "arial.ttf")
    for font_name in font_names:
        paths = [Path("C:/Windows/Fonts") / font_name, Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
        for p in paths:
            if p.exists(): return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()

async def build_profile_card(member, user_data, profile_data, background_bytes=None, stats_data=None):
    # 1. Khởi tạo Background
    if background_bytes:
        try:
            bg = Image.open(BytesIO(background_bytes)).convert("RGBA")
            bg = ImageOps.fit(bg, CARD_SIZE, centering=(0.5, 0.5))
        except:
            bg = Image.new("RGBA", CARD_SIZE, (20, 20, 25, 255))
    else:
        bg = Image.new("RGBA", CARD_SIZE, (20, 20, 25, 255))

    overlay = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 100))
    img = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(img)

    # 2. Vẽ Avatar bo tròn
    avatar_size = 200
    try:
        avatar_asset = member.display_avatar.with_size(256)
        avatar_img = Image.open(BytesIO(await avatar_asset.read())).convert("RGBA")
        avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.LANCZOS)
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        img.paste(avatar_img, (50, 50), mask)
        draw.ellipse((48, 48, 50+avatar_size+2, 50+avatar_size+2), outline=(102, 217, 196, 200), width=5)
    except: pass

    # 3. Thông tin văn bản
    draw.text((280, 60), member.display_name, fill=(255, 255, 255), font=_font(50, bold=True))
    
    level = profile_data[1] if profile_data else 1
    exp = profile_data[2] if profile_data else 0
    max_exp = level * 100 
    draw.text((280, 130), f"LEVEL {level}", fill=(102, 217, 196), font=_font(35, bold=True))

    # 4. Thanh kinh nghiệm (XP Bar)
    bar_x, bar_y, bar_w, bar_h = 280, 185, 650, 25
    ratio = min(exp / max_exp, 1.0) if max_exp > 0 else 0
    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=12, fill=(50, 50, 50, 200))
    if ratio > 0:
        draw.rounded_rectangle((bar_x, bar_y, bar_x + int(bar_w * ratio), bar_y + bar_h), radius=12, fill=(102, 217, 196))
    draw.text((bar_x, bar_y + 35), f"XP: {exp}/{max_exp}", fill=(200, 200, 200), font=_font(18))

    # 5. Khu vực Chỉ số (Stats)
    stats = stats_data or {"ATK": "0", "DEF": "0", "SPD": "0", "CRIT": "0%"}
    start_y = 350
    spacing_x = 220
    for i, (label, value) in enumerate(stats.items()):
        x_pos = 100 + (i * spacing_x)
        draw.rounded_rectangle((x_pos - 20, start_y, x_pos + 180, start_y + 120), radius=15, fill=(255, 255, 255, 20))
        draw.text((x_pos, start_y + 20), label, fill=(102, 217, 196), font=_font(22, bold=True))
        draw.text((x_pos, start_y + 60), str(value), fill=(255, 255, 255), font=_font(35, bold=True))

    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output