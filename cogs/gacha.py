import asyncio
import discord
from discord.ext import commands
from core.database import get_user, update_money
from core.gacha import summon_character
from core.game_data import RARITY_ORDER  # Import luôn thứ tự từ game_data cho đồng bộ
from core.ui import (
    get_rarity_icon,
    get_character_icon,
    get_icon,
    get_character_avatar
)
from core.cooldown import check_cooldown

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Link trực tiếp từ kênh Discord của bạn
        self.mythic_effect_url = "https://cdn.discordapp.com/attachments/1502488097307361290/1502488235010555944/gacha.gif?ex=69ffe4b6&is=69fe9336&hm=d4816c8bc44e45aef151fd4811cba40b58ba8db9ff15fd75ec19ca45c781b8ad&"

    @commands.command(name="cm", aliases=["chieumo", "achimi"])
    async def summon(self, ctx, times: str = "1"):
        user_id = str(ctx.author.id)
        
        # --- Xử lý tham số lượt quay ---
        times_str = times.lower().replace("x", "").strip()
        try:
            num_times = int(times_str)
        except ValueError:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Vui lòng dùng `hcm` hoặc `hcm 10` (hoặc `hcm x10`)")
        
        if num_times not in (1, 10):
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Chỉ có thể chiêu mộ 1 lần hoặc 10 lần!")

        # --- Kiểm tra Cooldown và Tiền ---
        ok, time_left = check_cooldown(user_id, "summon", 2)
        if not ok:
            return await ctx.send(f"⏳ Chờ {time_left}s để summon tiếp!")

        user = get_user(user_id)
        money = user[1]
        cost = 500 * num_times

        if money < cost:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn cần {cost} tiền! Hiện có: {money}")

        update_money(user_id, money - cost)

        # ==========================================
        # CHIÊU MỘ x1
        # ==========================================
        if num_times == 1:
            result = summon_character(user_id)
            rarity = result['rarity']

            # Hiệu ứng chờ 2 giây nếu quay trúng Mythic/Legendary/Godlike
            if rarity in ["Mythic", "Legendary", "Godlike"]:
                waiting_embed = discord.Embed(
                    title=f"🔮 {ctx.author.display_name} ĐANG lậy bố...",
                    description="Linh khí đang tụ hội, thiên mệnh đang xoay vần... Đạo hữu hãy kiên nhẫn chờ đợi tuyệt tác xuất thế!",
                    color=0xe74c3c
                )
                waiting_embed.set_image(url=self.mythic_effect_url)
                msg = await ctx.send(embed=waiting_embed)
                
                await asyncio.sleep(9) 
                await msg.delete()

            # Hiển thị kết quả Embed x1
            rarity_icon = get_rarity_icon(rarity, ctx.guild, ctx.bot)
            char_icon = get_character_icon(result['name'], result['class'], ctx.guild, ctx.bot)
            stats = result["stats"]
            
            embed = discord.Embed(
                title=f"{rarity_icon} {ctx.author.display_name} đã nhận được {rarity_icon}",
                color=0xe74c3c if rarity in ["Mythic", "Legendary", "Godlike"] else 0x2F3136
            )
            
            avatar_url = get_character_avatar(result['name'], result['class'], ctx.guild, ctx.bot)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

            embed.add_field(
                name="Thông tin", 
                value=f"**Tướng:** {char_icon} {result['name']}\n**Độ hiếm:** {rarity_icon} `{rarity}`\n**Hệ:** {get_icon(result['class'], ctx.guild, ctx.bot)} {result['class']}", 
                inline=False
            )

            # Chỉ số chi tiết (Chia 2 cột)
            stat_col1 = (
                f"{get_icon('atk_phys', ctx.guild, ctx.bot)} ATK: `{stats['atk_phys']}`\n"
                f"{get_icon('def_phys', ctx.guild, ctx.bot)} DEF: `{stats['def_phys']}`\n"
                f"{get_icon('hp', ctx.guild, ctx.bot)} HP: `{stats['hp']}`"
            )
            stat_col2 = (
                f"{get_icon('atk_magic', ctx.guild, ctx.bot)} MATK: `{stats['atk_magic']}`\n"
                f"{get_icon('def_magic', ctx.guild, ctx.bot)} MDEF: `{stats['def_magic']}`\n"
                f"{get_icon('spd', ctx.guild, ctx.bot)} SPD: `{stats['spd']}` | {get_icon('crit', ctx.guild, ctx.bot)} `{stats['crit']}%`"
            )
            embed.add_field(name="⚔️ Chỉ số cơ bản", value=stat_col1, inline=True)
            embed.add_field(name="🪄 Chỉ số phụ", value=stat_col2, inline=True)
            
            embed.set_footer(text=f"Sở hữu bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

        # ==========================================
        # CHIÊU MỘ x10
        # ==========================================
        else:
            results = []
            has_mythic = False
            for _ in range(num_times):
                res = summon_character(user_id)
                results.append(res)
                if res['rarity'] in ["Mythic", "Legendary", "Godlike"]:
                    has_mythic = True

            # Hiệu ứng nếu trong 10 lượt có Mythic
            if has_mythic:
                waiting_embed = discord.Embed(
                    title=f"🔮 {ctx.author.display_name} UI UI UI Lỗ rồi Lổ rồi ...",
                    description="ui ui ui cailon gì đang rơi xuống kìa !",
                    color=0xe74c3c
                )
                waiting_embed.set_image(url=self.mythic_effect_url)
                msg = await ctx.send(embed=waiting_embed)
                
                # SỬA Ở ĐÂY: Giảm từ 9 giây xuống 3 giây để bot phản hồi mượt hơn
                await asyncio.sleep(9)
                await msg.delete()

            # Bảng tổng kết x10
            rarity_counts = {}
            for r in results:
                rarity_counts[r['rarity']] = rarity_counts.get(r['rarity'], 0) + 1
            
            embed = discord.Embed(title=f"🎲 {ctx.author.display_name} Đã Chiêu Mộ 10 Lần ", color=0x2ecc71)
            
            # Thống kê độ hiếm (ĐÃ FIX: Lấy danh sách từ file game_data)
            count_str = ""
            for r_name in RARITY_ORDER:
                if r_name in rarity_counts:
                    icon = get_rarity_icon(r_name, ctx.guild, ctx.bot)
                    count_str += f"{icon} {r_name}: **{rarity_counts[r_name]}**\n"
            embed.add_field(name="📊 Tổng kết", value=count_str, inline=False)

            # Danh sách chi tiết
            details = ""
            for i, res in enumerate(results, 1):
                r_icon = get_rarity_icon(res['rarity'], ctx.guild, ctx.bot)
                c_icon = get_character_icon(res['name'], res['class'], ctx.guild, ctx.bot)
                
                # Làm nổi bật nếu trúng hàng xịn
                if res['rarity'] in ["Legendary", "Godlike"]:
                    details += f"{i}. {r_icon} {c_icon} **{res['name']}** ✨\n"
                else:
                    details += f"{i}. {r_icon} {c_icon} **{res['name']}**\n"
            
            embed.add_field(name="📋 Chi tiết", value=details, inline=False)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Gacha(bot))