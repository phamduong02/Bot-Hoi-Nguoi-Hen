import datetime
import random
import discord
from discord.ext import commands

from core.database import (
    add_user_item, add_weapon, add_weapon_chests, 
    get_user, get_weapon_chests, update_money
)
from core.shop_data import SHOP_ITEMS, get_item_by_id
from core.ui import get_weapon_icon, get_icon
from core.weapon_data import generate_weapon_instance

# =========================================================
# HÀM RANDOM VŨ KHÍ HẰNG NGÀY
# =========================================================
def get_daily_shop_weapons():
    today = datetime.date.today()
    rng = random.Random(f"shop_{today.year}_{today.month}_{today.day}")

    base_prices = {
        "Common": 1500, "Uncommon": 3000, "Rare": 7000,
        "Epic": 15000, "Mythic": 40000, "Legendary": 100000, "Godlike": 300000,
    }

    daily_items = []
    for _ in range(10):
        w = generate_weapon_instance(rng=rng)
        base_price = base_prices.get(w["rarity"], 1000)
        w["price"] = int(base_price * rng.uniform(0.9, 1.1))
        daily_items.append(w)

    return daily_items

# =========================================================
# MENU THẢ XUỐNG (DROPDOWN)
# =========================================================
class ShopSelect(discord.ui.Select):
    def __init__(self, daily_weapons, bot, guild):
        self.daily_weapons = daily_weapons
        self.bot = bot
        self.guild = guild
        options = []

        for index, w in enumerate(daily_weapons):
            raw_emoji = get_weapon_icon(w.get("emoji", ""), guild, bot)
            safe_emoji = raw_emoji if str(raw_emoji).startswith("<") else "🗡️"

            # ĐÃ SỬA: Xóa phần độ hiếm khỏi description để tránh lỗi Custom Emoji của Discord
            options.append(discord.SelectOption(
                label=w['name'],
                description=f"🪙 {w['price']} Gold",
                value=str(index),
                emoji=safe_emoji,
            ))

        super().__init__(
            placeholder="Mở để chọn vũ khí muốn mua...",
            min_values=1, max_values=1,
            options=options or [discord.SelectOption(label="Shop trống", value="0")]
        )

    async def callback(self, interaction: discord.Interaction):
        w = self.daily_weapons[int(self.values[0])]
        user_id = str(interaction.user.id)
        current_money = get_user(user_id)[1]
        cost = int(w.get("price", 0))
        gold_icon = get_icon("gold", interaction.guild, self.bot)

        if current_money < cost:
            return await interaction.response.send_message(
                f"{get_icon('cross', interaction.guild, self.bot)} Bạn không đủ tiền!\n"
                f"Cần: `{gold_icon} {cost}`\nHiện có: `{gold_icon} {current_money}`",
                ephemeral=True
            )

        update_money(user_id, current_money - cost)
        stats = dict(w["stats"])
        stats.update({"rarity": w.get("rarity"), "rarity_roll": w.get("rarity_roll", 0)})
        add_weapon(user_id, w["code"], stats)

        w_emoji = get_weapon_icon(w.get("emoji", ""), self.guild, self.bot)
        stat_str = " | ".join([f"{get_icon(k, self.guild, self.bot)} {v}" for k, v in w["stats"].items()]) or "—"

        await interaction.response.send_message(
            f"🎉 **{interaction.user.display_name}** đã mua {w_emoji} **{w['name']}** với giá `{gold_icon} {cost}`!\n"
            f"📊 {stat_str}", ephemeral=True
        )

class ShopView(discord.ui.View):
    def __init__(self, daily_weapons, bot, guild):
        super().__init__(timeout=60)
        self.add_item(ShopSelect(daily_weapons, bot, guild))

# =========================================================
# LỆNH CHÍNH (SHOP DISPLAY)
# =========================================================
class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop", aliases=["cuahang"])
    async def show_shop(self, ctx):
        daily_weapons = get_daily_shop_weapons()
        gold_icon = get_icon("gold", ctx.guild, self.bot)

        embed = discord.Embed(
            title="🏪 Chợ Đen Vũ Khí",
            description="HÔM NAY CHÚNG TA SẼ CÓ CÁI GÌ ĐÂYYYYYY.\nBẮN TIM PĂNG PĂNG PĂNG!",
            color=0x2C3E50,
        )

        for w in daily_weapons:
            emoji = get_weapon_icon(w.get("emoji", ""), ctx.guild, self.bot)
            
            # LẤY EMOJI ĐỘ HIẾM TỪ SERVER
            r_icon = get_icon(w["rarity"].lower(), ctx.guild, self.bot)
            if not r_icon or not str(r_icon).startswith("<"):
                fallback = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣", "Mythic": "🔴", "Legendary": "🟡", "Godlike": "✨"}
                r_icon = fallback.get(w["rarity"], "⚪")

            # Lấy icon chỉ số từ server
            stat_lines = "\n".join([f"{get_icon(k, ctx.guild, self.bot)} **{v}**" for k, v in w["stats"].items()]) or "└ —"

            embed.add_field(
                name=f"{emoji} {w['name']}",
                value=(
                    f"Giá: {gold_icon} **{w['price']}**\n"
                    f"Độ hiếm: {r_icon} (`{w.get('rarity_roll',0)}%`)\n"
                    f"{stat_lines}\n"
                    f"✨ {w.get('passive_text','')}"
                ),
                inline=True
            )

        chest = SHOP_ITEMS.get("weapon_chest")
        if chest:
            embed.add_field(
                name=f"{chest.get('emoji','🎁')} {chest.get('name','Rương')}",
                value=f"Giá: {gold_icon} **{chest.get('price', 0)}**\n{chest.get('desc','')}\nDùng `hmua {chest.get('id','1')} <số_lượng>` để mua.",
                inline=False
            )

        embed.set_footer(text="Chọn vũ khí muốn mua ở menu bên dưới.")
        await ctx.send(embed=embed, view=ShopView(daily_weapons, ctx.bot, ctx.guild))

    @commands.command(name="mua", aliases=["buy"])
    async def buy_item(self, ctx, item_id: str, amount: str = "1"):
        user_id = str(ctx.author.id)
        gold_icon = get_icon("gold", ctx.guild, self.bot)

        try:
            qty = int(str(amount).lower().replace("x", "").strip())
        except ValueError:
            qty = 1
        qty = max(1, min(50, qty))

        key, item = get_item_by_id(str(item_id))
        if not item:
            return await ctx.send(f"{get_icon('cross', ctx.guild, self.bot)} Không tìm thấy món này.")

        user = get_user(user_id)
        current_money = user[1]
        cost = int(item.get("price", 0)) * qty

        if current_money < cost:
            return await ctx.send(
                f"{get_icon('cross', ctx.guild, self.bot)} Bạn không đủ tiền!\n"
                f"Cần `{gold_icon} {cost}`\nBạn có `{gold_icon} {current_money}`"
            )

        update_money(user_id, current_money - cost)

        if item.get("type") == "chest" and key == "weapon_chest":
            add_weapon_chests(user_id, qty)
            total = get_weapon_chests(user_id)
            return await ctx.send(f"🎁 Bạn đã mua **{item.get('name','Rương')}** x{qty} với giá `{gold_icon} {cost}`.\nHiện có: `{total}` rương.")

        add_user_item(user_id, key, qty)
        await ctx.send(f"{get_icon('tick', ctx.guild, self.bot)} Đã mua **{item.get('name','Item')}** x{qty} với giá `{gold_icon} {cost}`")

async def setup(bot):
    await bot.add_cog(Shop(bot))