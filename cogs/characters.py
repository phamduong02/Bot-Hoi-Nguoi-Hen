import discord
from discord.ext import commands
from core.database import get_characters, set_team, get_team, get_character_by_id
from core.game_data import RARITY_ORDER, CHARACTERS
from core.ui import get_rarity_icon, get_character_icon

RARITY_ROW_ORDER = list(RARITY_ORDER)
ITEMS_PER_RARITY_LINE = 5

# ================= HELPERS =================

def build_character_group_ids(chars):
    grouped = {}
    for c in chars:
        key = (c[2], c[3], c[4]) # Name, Class, Rarity
        if key not in grouped:
            grouped[key] = {
                "ids": [],
                "name": c[2],
                "cls": c[3],
                "rarity": c[4]
            }
        grouped[key]["ids"].append(c[0])

    rarity_index = {rarity: index for index, rarity in enumerate(RARITY_ROW_ORDER)}
    character_order = {
        character["name"]: index
        for index, character in enumerate(CHARACTERS)
    }

    groups = sorted(
        grouped.values(),
        key=lambda group: (
            rarity_index.get(group["rarity"], len(RARITY_ROW_ORDER)),
            character_order.get(group["name"], len(character_order)),
            group["name"].casefold()
        )
    )

    group_ids = {}
    for group_id, group in enumerate(groups, start=1):
        group["group_id"] = group_id
        group_ids[group_id] = group

    return group_ids

def chunk_items(items, size):
    return [items[index:index + size] for index in range(0, len(items), size)]

# ================= UI COMPONENTS =================

import discord
from discord.ext import commands
from core.database import get_characters, set_team, get_team, get_character_by_id
from core.game_data import RARITY_ORDER, CHARACTERS
from core.ui import get_rarity_icon, get_character_icon, get_icon

RARITY_ROW_ORDER = list(RARITY_ORDER)

# ================= UI COMPONENTS =================

class SlotSelect(discord.ui.Select):

    def __init__(self, slot_idx, page_groups, current_gid, guild, bot):

        self.slot_idx = slot_idx

        options = [
            discord.SelectOption(
                label="-- Bỏ trống Slot này --",
                value="none",
                emoji="🚫"
            )
        ]

        for gid, group in page_groups:

            is_default = (gid == current_gid)

            # =========================
            # LOAD CUSTOM EMOJI
            # =========================

            discord_emoji = None

            try:

                emoji_str = get_character_icon(
                    group['name'],
                    group['cls'],
                    guild,
                    bot
                )

                # custom emoji
                if emoji_str.startswith("<:") or emoji_str.startswith("<a:"):

                    emoji_id = int(
                        emoji_str.split(":")[-1].replace(">", "")
                    )

                    discord_emoji = bot.get_emoji(emoji_id)

                else:
                    discord_emoji = emoji_str

            except:
                discord_emoji = "👤"

            # =========================
            # OPTION
            # =========================

            options.append(
                discord.SelectOption(
                    label=f"{group['name']} (x{len(group['ids'])})",
                    value=str(gid),
                    description=f"{group['rarity']} | {group['cls']}",
                    emoji=discord_emoji,
                    default=is_default
                )
            )

        super().__init__(
            placeholder=f"Chọn tướng cho Slot {slot_idx + 1}...",
            options=options,
            row=slot_idx
        )

    async def callback(self, interaction: discord.Interaction):

        val = self.values[0]

        self.view.selected_gids[self.slot_idx] = (
            None if val == "none" else int(val)
        )

        await self.view.save_team(interaction)

class AdvancedChooseTeamView(discord.ui.View):
    def __init__(self, user_id, group_ids, current_gids, guild, bot):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.group_ids = list(group_ids.items()) # Chuyển dict sang list để slice trang
        self.selected_gids = current_gids 
        self.guild = guild
        self.bot = bot
        self.page = 0
        self.items_per_page = 24 # Tối đa cho mỗi trang

        self.update_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == str(self.user_id):
            return True
        await interaction.response.send_message(
            f"{get_icon('cross', interaction.guild, interaction.bot)} Đây không phải menu chọn team của bạn.",
            ephemeral=True,
        )
        return False

    def update_components(self):
        self.clear_items()
        
        # Lấy danh sách tướng cho trang hiện tại
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_groups = self.group_ids[start:end]

        # Thêm 3 Menu chọn Slot
        for i in range(3):
            self.add_item(SlotSelect(i, page_groups, self.selected_gids[i], self.guild, self.bot))

        # Thêm nút điều hướng trang
        total_pages = (len(self.group_ids) - 1) // self.items_per_page + 1
        
        prev_btn = discord.ui.Button(label="◀️", style=discord.ButtonStyle.gray, disabled=(self.page == 0), row=4)
        prev_btn.callback = self.prev_page
        self.add_item(prev_btn)

        page_btn = discord.ui.Button(label=f"Trang {self.page + 1}/{total_pages}", style=discord.ButtonStyle.secondary, disabled=True, row=4)
        self.add_item(page_btn)

        next_btn = discord.ui.Button(label="▶️", style=discord.ButtonStyle.gray, disabled=(end >= len(self.group_ids)), row=4)
        next_btn.callback = self.next_page
        self.add_item(next_btn)

    async def prev_page(self, interaction: discord.Interaction):
        self.page -= 1
        self.update_components()
        await interaction.response.edit_message(content=self.get_status_text(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.page += 1
        self.update_components()
        await interaction.response.edit_message(content=self.get_status_text(), view=self)

    async def save_team(self, interaction: discord.Interaction):
        actual_ids = []
        counts = {}
        # Chuyển đổi list group_ids về lại dạng dict để lấy thông tin ids nhanh
        full_groups = dict(self.group_ids)
        
        for gid in self.selected_gids:
            if gid is None:
                actual_ids.append(None)
                continue
            group = full_groups.get(gid)
            used = counts.get(gid, 0)
            if group and used < len(group["ids"]):
                actual_ids.append(group["ids"][used])
                counts[gid] = used + 1
            else:
                actual_ids.append(None)

        set_team(self.user_id, actual_ids[0], actual_ids[1], actual_ids[2])
        await interaction.response.edit_message(content=self.get_status_text(), view=self)

    def get_status_text(self):
        msg = "⚔️ **BATTLE SETTINGS (ĐỘI HÌNH HIỆN TẠI)**\n"
        full_groups = dict(self.group_ids)
        for i, gid in enumerate(self.selected_gids):
            group = full_groups.get(gid) if gid else None
            if group:
                r_icon = get_rarity_icon(group['rarity'], self.guild, self.bot)
                c_icon = get_character_icon(group['name'], group['cls'], self.guild, self.bot)
                name = f"{r_icon} {c_icon} **{group['name']}**"
            else:
                name = "🚫 `Trống`"
            msg += f"**Animal in Team Slot {i+1}:** {name}\n"
        return msg

# ================= MAIN COG =================

class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nhanvat", aliases=["chars", "nv", "hnv"])
    async def chars(self, ctx):
        user_id = str(ctx.author.id)
        chars = get_characters(user_id)
        if not chars:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn chưa có nhân vật nào!")

        group_ids = build_character_group_ids(chars)
        rarity_counts = {}
        for group in group_ids.values():
            r = group["rarity"]
            rarity_counts[r] = rarity_counts.get(r, 0) + len(group["ids"])

        total_chars = sum(len(g["ids"]) for g in group_ids.values())
        embed = discord.Embed(
            title=f"📜 Nhân vật của {ctx.author.name}",
            description=f"**Tổng nhân vật:** {total_chars} | **Tổng nhóm:** {len(group_ids)}\nSử dụng `hchontuong` để set team.",
            color=0x2F3136
        )

        for rarity in RARITY_ROW_ORDER:
            r_groups = [g for g in group_ids.values() if g["rarity"] == rarity]
            if r_groups:
                items = []

                for g in r_groups:

                    icon = get_character_icon(
                        g['name'],
                        g['cls'],
                        ctx.guild,
                        self.bot
                    )

                    items.append(
                        f"`{g['group_id']}` {icon} x{len(g['ids'])}"
                    )
                value = "\n".join("  ".join(line) for line in chunk_items(items, ITEMS_PER_RARITY_LINE))
                embed.add_field(name=f"{get_rarity_icon(rarity, ctx.guild, self.bot)} {rarity}", value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="chontuong", aliases=["setteam", "hchontuong"])
    async def team(self, ctx, *raw_ids: str):
        user_id = str(ctx.author.id)
        chars = get_characters(user_id)
        if not chars:
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn chưa có nhân vật nào!")

        group_ids = build_character_group_ids(chars)
        team_data = get_team(user_id)
        
        current_gids = [None, None, None]
        if team_data:
            for i, char_id in enumerate(team_data[1:]):
                if char_id:
                    for gid, g in group_ids.items():
                        if char_id in g["ids"]:
                            current_gids[i] = gid
                            break

        # Set nhanh bằng ID nhóm (VD: hchontuong 1 3 5) để tránh "Too many arguments" bị im lặng
        if raw_ids:
            if len(raw_ids) > 3:
                return await ctx.send(
                    f"{get_icon('cross', ctx.guild, ctx.bot)} Sai cú pháp.\n"
                    "Dùng `hchontuong` để mở menu chọn team, hoặc `hchontuong <id1> <id2> <id3>` để set nhanh.\n"
                    "Ví dụ: `hchontuong 1 3 5`"
                )

            parsed_ids = []
            for token in raw_ids:
                t = str(token).strip().lower()
                if t in {"0", "none", "null", "-", "_"}:
                    parsed_ids.append(None)
                    continue
                try:
                    parsed_ids.append(int(t))
                except ValueError:
                    return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} ID không hợp lệ: `{token}` (chỉ nhận số hoặc `none`).")

            while len(parsed_ids) < 3:
                parsed_ids.append(None)

            # map group_id -> actual character ids (hỗ trợ chọn trùng nhóm nếu có nhiều bản sao)
            actual_ids = []
            used_counts = {}
            for gid in parsed_ids:
                if gid is None:
                    actual_ids.append(None)
                    continue
                group = group_ids.get(gid)
                if not group:
                    return await ctx.send(
                        f"{get_icon('cross', ctx.guild, ctx.bot)} Không tìm thấy **ID nhóm** `{gid}`.\n"
                        "Dùng `hchontuong` để mở menu và xem nhóm tướng hợp lệ."
                    )
                used = used_counts.get(gid, 0)
                if used >= len(group["ids"]):
                    actual_ids.append(None)
                else:
                    actual_ids.append(group["ids"][used])
                    used_counts[gid] = used + 1

            set_team(user_id, actual_ids[0], actual_ids[1], actual_ids[2])

            msg = f"{get_icon('tick', ctx.guild, ctx.bot)} **Đã set team:**\n"
            for i, (gid, char_id) in enumerate(zip(parsed_ids, actual_ids), start=1):
                if gid is None or char_id is None:
                    msg += f"Slot {i}: 🚫 `Trống`\n"
                    continue
                group = group_ids.get(gid)
                if not group:
                    msg += f"Slot {i}: 🚫 `Trống`\n"
                    continue
                msg += (
                    f"Slot {i}: "
                    f"{get_rarity_icon(group['rarity'], ctx.guild, self.bot)} "
                    f"{get_character_icon(group['name'], group['cls'], ctx.guild, self.bot)} "
                    f"**{group['name']}** (Group `{gid}`)\n"
                )
            return await ctx.send(msg)

        # Truyền thêm guild và bot vào View để lấy Emoji
        view = AdvancedChooseTeamView(user_id, group_ids, current_gids, ctx.guild, self.bot)
        try:
            await ctx.send(content=view.get_status_text(), view=view)
        except discord.HTTPException as exc:
            await ctx.send(
                "❌ Không thể mở menu chọn team (thường do emoji/components bị Discord từ chối).\n"
                "Bạn có thể set nhanh bằng ID nhóm:\n"
                "`hchontuong <id1> [id2] [id3]`\n"
                f"Lỗi: `{type(exc).__name__}`"
            )

    @commands.command(name="team")
    async def myteam(self, ctx):
        user_id = str(ctx.author.id)
        team = get_team(user_id)
        if not team or not any(team[1:]):
            return await ctx.send(f"{get_icon('cross', ctx.guild, ctx.bot)} Bạn chưa set team!")

        msg = "⚔️ **Team của bạn:**\n\n"
        for slot in team[1:]:
            if slot:
                char = get_character_by_id(slot, user_id)
                if char:
                    msg += f"{get_rarity_icon(char[4], ctx.guild, self.bot)} {get_character_icon(char[2], char[3], ctx.guild, self.bot)} **{char[2]}**\n"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Characters(bot))
