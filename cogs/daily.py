import datetime
import random
import discord
from discord.ext import commands

from core.database import (
    get_user,
    update_money,
    add_exp,
    add_weapon,
    get_daily_claim,
    set_daily_claim,
)
from core.weapon_data import generate_weapon_instance
from core.ui import get_weapon_icon, get_icon

# ── Cấu hình ──────────────────────────────────────────────────────────
GOLD_MIN = 500 
GOLD_MAX = 2000
EXP_MIN = 10
EXP_MAX = 30

STREAK_CONFIG = {
    1: {"bonus_gold":    0, "exp":  20, "weapon_chance": 0.00},
    2: {"bonus_gold":    0, "exp":  25, "weapon_chance": 0.00},
    3: {"bonus_gold":  300, "exp":  30, "weapon_chance": 0.30},
    4: {"bonus_gold":    0, "exp":  35, "weapon_chance": 0.00},
    5: {"bonus_gold":  500, "exp":  40, "weapon_chance": 0.50},
    6: {"bonus_gold":    0, "exp":  60, "weapon_chance": 0.00},
    7: {"bonus_gold": 1000, "exp": 100, "weapon_chance": 1.00},
}

COLOR_MAP = {
    1: 0x95a5a6, 2: 0x2ecc71, 3: 0x3498db,
    4: 0x9b59b6, 5: 0xe67e22, 6: 0xe74c3c, 7: 0xf1c40f,
}

TZ_VN = datetime.timezone(datetime.timedelta(hours=7))

# ── Helpers ──────────────────────────────────────────────────────────────────

def _now_vn():
    return datetime.datetime.now(tz=TZ_VN)

def _today():
    return _now_vn().date()

def _roll_reward(streak: int):
    day = min(streak, 7)
    cfg = STREAK_CONFIG[day]
    base_gold = random.randint(GOLD_MIN, GOLD_MAX)
    base_exp = random.randint(EXP_MIN, EXP_MAX)
    return {
        "total_gold": base_gold + cfg["bonus_gold"],
        "bonus_gold": cfg["bonus_gold"],
        "total_exp": base_exp + cfg["exp"],
        "weapon_chance": cfg["weapon_chance"],
    }

def _build_streak_bar(streak: int):
    display = min(streak, 7)
    return " ".join([get_icon('tick', None, None) if i < display else get_icon('star', None, None) if i == display else get_icon('white_large_square', None, None) for i in range(1, 8)])

def _generate_random_weapon():
    return generate_weapon_instance()

def _build_embed(ctx, bot, author, streak, reward, weapon_dropped, current_money):
    day = min(streak, 7)
    color = COLOR_MAP.get(day, 0xf1c40f)
    
    embed = discord.Embed(
        title=f"🗓️ Điểm danh ngày {day} {'🔥' if streak >= 7 else '⭐'}",
        description=f"Chào **{author.display_name}**!\nStreak: **{streak} ngày**\n\n{_build_streak_bar(streak)}",
        color=color
    )

    reward_text = f"💰 **+{reward['total_gold']:,} Gold**"
    if reward['bonus_gold'] > 0:
        reward_text += f" (Bonus: `+{reward['bonus_gold']:,}`)"
    
    reward_text += f"\n⭐ **+{reward['total_exp']} EXP**"

    if weapon_dropped:
        w = weapon_dropped
        stat_str = " | ".join([f"{k.upper()}: {v}" for k, v in w["stats"].items()]) or "—"
        wp_emoji = get_weapon_icon(w.get("emoji", ""), ctx.guild, bot)
        reward_text += (
            f"\n\n🎁 **Rơi Trang Bị:** [**{w.get('rarity','Common')}**] (roll `{w.get('rarity_roll',0)}%`) "
            f"{wp_emoji} **{w.get('name','Weapon')}**\n"
            f"└ 📊 `{stat_str}`\n"
            f"└ ✨ {w.get('passive_text','')}"
        )

    embed.add_field(name="Phần thưởng", value=reward_text, inline=False)
    embed.add_field(name="👛 Ví hiện tại", value=f"**{current_money:,} Gold**", inline=True)
    embed.set_thumbnail(url=author.display_avatar.url)
    return embed

# ── Cog ──────────────────────────────────────────────────────────────────────

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hdaily", aliases=["daily", "diemdanh"])
    async def daily(self, ctx):
        user_id = str(ctx.author.id)
        today = _today()
        
        get_user(user_id) 
        row = get_daily_claim(user_id)

        if row:
            _, last_str, streak = row
            if datetime.date.fromisoformat(last_str) == today:
                next_midnight = datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time.min, tzinfo=TZ_VN)
                rem = next_midnight - _now_vn()
                h, m = divmod(int(rem.total_seconds()), 3600)
                
                emb = discord.Embed(title="⏳ Đã điểm danh!", description=f"Hẹn gặp lại sau **{h}h {m//60}m**!", color=0xe74c3c)
                emb.add_field(name="🔥 Streak", value=f"**{streak} ngày**\n{_build_streak_bar(streak)}")
                return await ctx.send(embed=emb)
            
            new_streak = streak + 1 if (today - datetime.date.fromisoformat(last_str)).days == 1 else 1
        else:
            new_streak = 1

        reward = _roll_reward(new_streak)
        weapon_dropped = None
        if random.random() < reward["weapon_chance"]:
            weapon_dropped = _generate_random_weapon()

        # Cập nhật DB
        user = get_user(user_id)
        new_money = user[1] + reward["total_gold"]
        update_money(user_id, new_money)
        add_exp(user_id, reward["total_exp"])
        
        if weapon_dropped:
            st = dict(weapon_dropped["stats"])
            st["rarity"] = weapon_dropped.get("rarity")
            st["rarity_roll"] = weapon_dropped.get("rarity_roll", 0)
            add_weapon(user_id, weapon_dropped["code"], st)
            
        set_daily_claim(user_id, today.isoformat(), new_streak)

        # Gửi kết quả (Lưu ý truyền đủ self.bot)
        embed = _build_embed(ctx, self.bot, ctx.author, new_streak, reward, weapon_dropped, new_money)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Daily(bot))
