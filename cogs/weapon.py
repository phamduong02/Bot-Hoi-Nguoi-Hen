import discord
from discord.ext import commands

from core.database import get_weapons
from core.ui import get_weapon_icon, get_icon
from core.weapon_data import WEAPONS, describe_passive


class Weapon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vk", aliases=["vukhi", "kho"])
    async def inventory(self, ctx):
        user_id = str(ctx.author.id)
        weapons = get_weapons(user_id)

        if not weapons:
            return await ctx.send("🎒 Kho vũ khí của bạn đang trống! Dùng `hshop` để mua hoặc `hmoruong` để mở rương.")

        embed = discord.Embed(
            title=f"🎒 KHO VŨ KHÍ CỦA {ctx.author.display_name.upper()}",
            color=0x3498DB,
        )

        desc = ""
        for w in weapons:
            w_id = w[0]
            w_code = w[1]
            equipped_to = w[8]
            hp = int((w[9] if len(w) > 9 else 0) or 0)
            rarity_roll = int(w[11] if len(w) > 11 and w[11] is not None else 0)

            base_w = WEAPONS.get(w_code)
            if not base_w:
                continue

            name = base_w.get("name", w_code)
            rarity = (w[10] if len(w) > 10 else None) or base_w.get("rarity", "Common")
            emoji = get_weapon_icon(base_w.get("emoji", ""), ctx.guild, self.bot)
            passive_text = describe_passive(base_w.get("passive") or {})

            stats = []
            if hp and hp > 0:
                stats.append(f"HP: {hp}")
            if w[2] > 0:
                stats.append(f"ATK: {w[2]}")
            if w[3] > 0:
                stats.append(f"MATK: {w[3]}")
            if w[4] > 0:
                stats.append(f"DEF: {w[4]}")
            if w[5] > 0:
                stats.append(f"MDEF: {w[5]}")
            if w[6] > 0:
                stats.append(f"CRIT: {w[6]}%")
            if w[7] > 0:
                stats.append(f"SPD: {w[7]}")

            stat_str = " | ".join(stats) if stats else "—"
            equip_str = f" `[Đang trang bị: Tướng #{equipped_to}]`" if equipped_to and equipped_to > 0 else ""
            roll_str = f" (roll `{rarity_roll}%`)" if rarity_roll > 0 else ""

            desc += (
                f"**ID: {w_id}** - {emoji} **{name}** `[{rarity}]`{roll_str}\n"
                f"└ 📊 `{stat_str}`{equip_str}\n"
                f"└ ✨ {passive_text}\n\n"
            )

        if len(desc) > 3900:
            desc = desc[:3900] + "\n...(còn nữa)"

        embed.description = desc
        embed.set_footer(text="Dùng `hwp` để mở giao diện trang bị cho tướng.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Weapon(bot))
