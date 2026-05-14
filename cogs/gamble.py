
import asyncio, json, random, time
from dataclasses import dataclass
from io import BytesIO
from itertools import combinations

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from core.database import get_user, update_money

from collections import deque
from core.ui import get_icon
# ─── Config ───────────────────────────────────────────────────────────────────
SESSION_SECONDS = 45
MAX_BET         = 500_000
DICE_SIZE       = 128
DICE_PAD        = 22

DICE_FACES      = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"}
DICE_EMOJI_NAMES= {1:"hnh_dice1",2:"hnh_dice2",3:"hnh_dice3",
                   4:"hnh_dice4",5:"hnh_dice5",6:"hnh_dice6"}

TOTAL_PAYOUT = {4:60,5:20,6:18,7:12,8:8,
                9:6,10:6,11:6,12:6,
                13:8,14:12,15:18,16:20,17:60}

GAME_HISTORY = deque(maxlen=15)

# ─── Evaluate ─────────────────────────────────────────────────────────────────
def _counts(dice): return {i:dice.count(i) for i in range(1,7)}
def _triple(dice):  return len(set(dice))==1

def evaluate(bt, bv, dice):
    t=sum(dice); c=_counts(dice); tr=_triple(dice)
    if bt=="big":    return (11<=t<=17) and not tr, 1
    if bt=="small":  return (4<=t<=10)  and not tr, 1
    if bt=="even":   return t%2==0, 1
    if bt=="odd":    return t%2==1, 1
    if bt=="total":  return t==bv, TOTAL_PAYOUT.get(bv,0)
    if bt=="any_triple":       return tr, 30
    if bt=="specific_triple":  return tr and dice[0]==bv, 180
    if bt=="double":           return c.get(bv,0)>=2, 11
    if bt=="combo":
        a,b=bv; return c.get(a,0)>=1 and c.get(b,0)>=1 and not tr, 6
    if bt=="single":
        n=c.get(bv,0)
        return n>0, min(n,3)
    return False,0

def blabel(bt,bv):
    if bt=="big":              return "🔴 Tài (11–17)"
    if bt=="small":            return "🟢 Xỉu (4–10)"
    if bt=="even":             return "⚫ Chẵn"
    if bt=="odd":              return "⚪ Lẻ"
    if bt=="total":            return f"Tổng {bv}"
    if bt=="any_triple":       return "💎 Bão"
    if bt=="specific_triple":  return f"🎯 Ba {bv}s"
    if bt=="double":           return f"👀 Đôi {bv}s"
    if bt=="combo":            a,b=bv; return f"🃏 Cặp {a}+{b}"
    if bt=="single":           return f"🎲 Mặt {bv}"
    return "?"

def bodds(bt,bv):
    if bt in("big","small","even","odd"): return "x1"
    if bt=="total":           return f"x{TOTAL_PAYOUT.get(bv,'?')}"
    if bt=="any_triple":      return "x30"
    if bt=="specific_triple": return "x180"
    if bt=="double":          return "x11"
    if bt=="combo":           return "x6"
    if bt=="single":          return "x1~3"
    return ""

def build_history_text():
    if not GAME_HISTORY:
        return "Chưa có dữ liệu"

    row1 = []
    row2 = []
    row3 = []

    for g in GAME_HISTORY:
        row1.append("🔴" if g["tai"] else "🟢")
        row2.append("⚫" if g["chan"] else "⚪")
        row3.append("💎" if g["bao"] else "➖")

    return (
        " ".join(row1) + "\n" +
        " ".join(row2) + "\n" +
        " ".join(row3)
    )
# ─── Dice image ───────────────────────────────────────────────────────────────
def _ffont(sz):
    for n in("seguisym.ttf","seguiemj.ttf","DejaVuSans.ttf","arial.ttf"):
        for p in(f"C:/Windows/Fonts/{n}",f"/usr/share/fonts/truetype/dejavu/{n}"):
            try: return ImageFont.truetype(p,sz)
            except OSError: pass
    return ImageFont.load_default()

def _eobj(val,guild):
    if not guild: return None
    t=DICE_EMOJI_NAMES[val].lower()
    for e in getattr(guild,"emojis",[]):
        if e.name.lower()==t: return e
    return None

def _dstr(dice,guild=None):
    parts=[]
    for v in dice:
        if guild:
            t=DICE_EMOJI_NAMES[v].lower()
            for e in getattr(guild,"emojis",[]):
                if e.name.lower()==t: parts.append(str(e)); break
            else: parts.append(DICE_FACES[v])
        else: parts.append(DICE_FACES[v])
    return "  ".join(parts)

async def build_dice_img(dice,guild=None):
    n=len(dice)
    W=DICE_PAD*(n+1)+DICE_SIZE*n; H=DICE_PAD*2+DICE_SIZE
    img=Image.new("RGBA",(W,H),(18,20,28,255))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle((0,0,W-1,H-1),radius=28,
        fill=(18,20,28,255),outline=(255,255,255,45),width=2)
    fn=_ffont(104); x=DICE_PAD
    for v in dice:
        eo=_eobj(v,guild); ei=None
        if eo:
            try: ei=Image.open(BytesIO(await eo.read())).convert("RGBA")
            except Exception: ei=None
        if ei:
            ei.thumbnail((DICE_SIZE,DICE_SIZE),Image.Resampling.LANCZOS)
            oy=DICE_PAD+(DICE_SIZE-ei.height)//2
            img.alpha_composite(ei,(x+(DICE_SIZE-ei.width)//2,oy))
        else:
            face=DICE_FACES[v]; bb=d.textbbox((0,0),face,font=fn)
            tw,th=bb[2]-bb[0],bb[3]-bb[1]
            d.text((x+(DICE_SIZE-tw)/2,DICE_PAD+(DICE_SIZE-th)/2-8),
                   face,font=fn,fill=(255,255,255,255))
        x+=DICE_SIZE+DICE_PAD
    buf=BytesIO(); img.save(buf,"PNG",optimize=True); buf.seek(0)
    return discord.File(buf,filename="dice.png")

# ─── Bet dataclass ────────────────────────────────────────────────────────────
@dataclass
class Bet:
    user_id: str; mention: str
    bt: str; bv: object; amount: int

# ─── Modal ────────────────────────────────────────────────────────────────────
class BetModal(discord.ui.Modal):
    amount=discord.ui.TextInput(label="Số tiền cược",
        placeholder=f"1 – {MAX_BET:,}",max_length=12)

    def __init__(self,session,bt,bv):
        super().__init__(title=f"Cược: {blabel(bt,bv)}  ({bodds(bt,bv)})")
        self.session=session; self.bt=bt; self.bv=bv

    async def on_submit(self,itr:discord.Interaction):
        raw=self.amount.value.replace(",","").replace(".","").strip()
        if not raw.isdigit() or int(raw)<=0:
            return await itr.response.send_message(f"{get_icon('cross', itr.guild, itr.client)} Số tiền không hợp lệ.",ephemeral=True)
        amt=int(raw)
        if amt>MAX_BET:
            return await itr.response.send_message(f"{get_icon('cross', itr.guild, itr.client)} Tối đa {MAX_BET:,}.",ephemeral=True)
        async with self.session.lock:
            if self.session.ended:
                return await itr.response.send_message(f"{get_icon('cross', itr.guild, itr.client)} Phiên đã kết thúc.",ephemeral=True)
            uid=str(itr.user.id)
            if uid in self.session.bets:
                b=self.session.bets[uid]
                return await itr.response.send_message(
                    f"{get_icon('cross', itr.guild, itr.client)} Bạn đã đặt cược `{blabel(b.bt,b.bv)}` · **{b.amount:,}** Gold rồi!",ephemeral=True)
            u=get_user(uid)
            if u[1]<amt:
                return await itr.response.send_message(
                    f"{get_icon('cross', itr.guild, itr.client)} Không đủ Gold. Hiện có: **{u[1]:,}**",ephemeral=True)
            update_money(uid,u[1]-amt)
            self.session.bets[uid]=Bet(uid,itr.user.mention,self.bt,self.bv,amt)
        await itr.response.send_message(
            f"{get_icon('tick', itr.guild, itr.client)} **{blabel(self.bt,self.bv)}** ({bodds(self.bt,self.bv)}) · **{amt:,}** Gold",
            ephemeral=True)
        await self.session.refresh()

# ─── Generic bet button ───────────────────────────────────────────────────────
class BB(discord.ui.Button):
    def __init__(self,sess,label,bt,bv,style,row,cid=None):
        super().__init__(label=label,style=style,row=row,
                         custom_id=cid)
        self.sess=sess; self.bt=bt; self.bv=bv
    async def callback(self,itr:discord.Interaction):
        if self.sess.ended:
            return await itr.response.send_message(f"{get_icon('cross', itr.guild, itr.client)} Phiên đã kết thúc.",ephemeral=True)
        await itr.response.send_modal(BetModal(self.sess,self.bt,self.bv))

# ─── Sub-views (ephemeral) ────────────────────────────────────────────────────
class SubView(discord.ui.View):
    def __init__(self,sess,cat):
        super().__init__(timeout=60)
        S=discord.ButtonStyle
        uid=id(sess)  # unique per session để tránh trùng custom_id
        if cat=="double":
            # 6 nút chia 2 hàng: 1-3 hàng 0, 4-6 hàng 1
            for v in range(1,7):
                row = 0 if v <= 3 else 1
                self.add_item(BB(sess,f"Đôi {v}s · x11","double",v,S.primary,row,
                                 cid=f"sub_d_{v}_{uid}"))
        elif cat=="triple":
            # 6 nút chia 2 hàng
            for v in range(1,7):
                row = 0 if v <= 3 else 1
                self.add_item(BB(sess,f"Ba {v}s · x180","specific_triple",v,S.danger,row,
                                 cid=f"sub_t_{v}_{uid}"))
        elif cat=="combo":
            # 15 cặp, 5 nút/hàng = 3 hàng
            for i,(a,b) in enumerate(combinations(range(1,7),2)):
                self.add_item(BB(sess,f"{a}+{b}","combo",(a,b),S.success,i//5,
                                 cid=f"sub_c_{a}{b}_{uid}"))
        elif cat=="single":
            # 6 nút chia 2 hàng: 1-3 hàng 0, 4-6 hàng 1
            for v in range(1,7):
                row = 0 if v <= 3 else 1
                self.add_item(BB(sess,f"Mặt {v}","single",v,S.secondary,row,
                                 cid=f"sub_s_{v}_{uid}"))

SUB_INFO={
    "double": ("👀 Đôi Cụ Thể · x11","≥2 trong 3 xúc xắc ra cùng mặt → thắng x11",0x3498db),
    "triple": ("🎯 Bão Cụ Thể · x180","Cả 3 xúc xắc ra đúng mặt bạn chọn → thắng x180 🔥",0xf1c40f),
    "combo":  ("🃏 Cặp Đôi · x6","2 mặt khác nhau cùng xuất hiện trong 3 xúc xắc\n(Không tính nếu là bão)",0x2ecc71),
    "single": ("🎲 Chọn Mặt · x1/x2/x3","Đoán mặt xúc xắc xuất hiện\n1 con trùng=x1 · 2 con trùng=x2 · 3 con trùng=x3",0xe67e22),
}

# ─── Nút mở sub-view ─────────────────────────────────────────────────────────
class OpenSubBtn(discord.ui.Button):
    def __init__(self,sess,label,cat,style,row):
        super().__init__(label=label,style=style,row=row)
        self.sess=sess; self.cat=cat
    async def callback(self,itr:discord.Interaction):
        if self.sess.ended:
            return await itr.response.send_message(f"{get_icon('cross', itr.guild, itr.client)} Phiên đã kết thúc.",ephemeral=True)
        title,desc,color=SUB_INFO[self.cat]
        embed=discord.Embed(title=title,description=desc,color=color)
        await itr.response.send_message(embed=embed,
            view=SubView(self.sess,self.cat),ephemeral=True)

# ─── Main View (23 nút, 5 hàng) ──────────────────────────────────────────────
class TaiXiuView(discord.ui.View):
    def __init__(self,sess):
        super().__init__(timeout=SESSION_SECONDS+10)
        self.sess=sess
        S=discord.ButtonStyle

        # ── Row 0: Big / Small / Chẵn / Lẻ / Any Triple ─────────────────────
        self.add_item(BB(sess,"🔴 Tài (11–17)","big",  None,S.danger,   0))
        self.add_item(BB(sess,"🟢 Xỉu (4–10)", "small",None,S.success,  0))
        self.add_item(BB(sess,"⚫ Chẵn",       "even", None,S.secondary,0))
        self.add_item(BB(sess,"⚪ Lẻ",         "odd",  None,S.secondary,0))
        self.add_item(BB(sess,"💎 Bão (x30)","any_triple",None,S.danger,0))

        # ── Row 1: Tổng 4–8 ──────────────────────────────────────────────────
        for v in range(4,9):
            self.add_item(BB(sess,f"{v}(x{TOTAL_PAYOUT[v]})","total",v,S.primary,1))

        # ── Row 2: Tổng 9–13 ─────────────────────────────────────────────────
        for v in range(9,14):
            self.add_item(BB(sess,f"{v}(x{TOTAL_PAYOUT[v]})","total",v,S.primary,2))

        # ── Row 3: Tổng 14–17 + Double ───────────────────────────────────────
        for v in range(14,18):
            self.add_item(BB(sess,f"{v}(x{TOTAL_PAYOUT[v]})","total",v,S.primary,3))
        self.add_item(OpenSubBtn(sess,"👀 Đôi (x11)","double",S.primary,3))

        # ── Row 4: Triple / Combo / Single ───────────────────────────────────
        self.add_item(OpenSubBtn(sess,"🎯 Bão cụ thể (x180)","triple",S.danger,  4))
        self.add_item(OpenSubBtn(sess,"🃏 Cặp Đôi (x6)",  "combo", S.success, 4))
        self.add_item(OpenSubBtn(sess,"🎲 Chọn Mặt","single",S.secondary,4))

    def disable_all(self):
        for item in self.children: item.disabled=True

# ─── Session ──────────────────────────────────────────────────────────────────
class TaiXiuSession:
    def __init__(self,cog,channel):
        self.cog=cog; self.channel=channel
        self.bets:dict[str,Bet]={}
        self.lock=asyncio.Lock()
        self.ended=False; self.message=None
        self.view=TaiXiuView(self)
        self.end_at=int(time.time())+SESSION_SECONDS

    def _open_embed(self):
        pot=sum(b.amount for b in self.bets.values())
        e=discord.Embed(title="🎲  Tài Xỉu Casino",color=0xe74c3c)
        e.description=(
            f"Phiên kết thúc <t:{self.end_at}:R>\n"
            "Bấm nút → nhập tiền → xác nhận\n"
            "Mỗi người **1 lần** / phiên · "
            f"Tối đa **{MAX_BET:,}** Gold\n"
            "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
        )
        e.add_field(name="👥 Số người cược",value=f"**{len(self.bets)}**",inline=True)
        e.add_field(name="💰 Tổng tiền",  value=f"**{pot:,}** Gold",  inline=True)
        e.add_field(name="⏳ Thời gian còn",   value=f"<t:{self.end_at}:R>",inline=True)
        e.add_field(name="📊 Bảng Tỉ Lệ",value=(
            "🔴 Tài/Xỉu · x1 (thua nếu Bão)\n"
            "⚫ Chẵn/Lẻ · x1  ·  💎 Bão · x30\n"
            "🔢 Số tổng · x6–x60  ·  👀 Đôi · x11\n"
            "🎯 Bão cụ thể · x180  ·  🃏 Cặp Đôi · x6\n"
            "🎲 Chọn Mặt · x1/x2/x3"
        ),inline=False)
        if self.bets:
            lines=[f"{b.mention} · `{blabel(b.bt,b.bv)}` · **{b.amount:,}**"
                   for b in list(self.bets.values())[-6:]]
            e.add_field(name="🗒️ Đặt cược gần đây",value="\n".join(lines),inline=False)
        e.set_footer(text="🎰 HoiNguoiHen Casino · Chơi có trách nhiệm!")
        return e

    def _closed_embed(self):
        e=self._open_embed()
        e.title="🎲  Tài Xỉu  —  Đã đóng cược"
        e.color=0x636e72; return e

    async def _result_embed(self,dice,total):
        tr=_triple(dice)
        rs="Tài 🔴" if total>=11 else "Xỉu 🟢"
        pr="Chẵn ⚫" if total%2==0 else "Lẻ ⚪"
        guild=getattr(self.channel,"guild",None)
        eg=self.cog.get_eg(guild)
        df=await build_dice_img(dice,eg)
        color=0xf1c40f if tr else (0x2ecc71 if total>=11 else 0x3498db)
        e=discord.Embed(title="🎲  Kết Quả Tài Xỉu",color=color)
        e.description=(
            f"{_dstr(dice,eg)}\n\n"
            f"**Tổng: {total}** · **{rs}** · **{pr}**"
            +(f"\n⚡ **Bão {dice[0]}s! BÃO!**" if tr else "")
            +"\n▰▰▰▰ Mấy con gà :))▰▰▰▰"
        )
        e.set_image(url="attachment://dice.png")
        if not self.bets:
            e.add_field(name="📋 Kết quả",value="Không có ai đặt cược trong phiên này.",inline=False)
            return e,df
        e.add_field(
            name="📜 Lịch sử gần đây",
            value=build_history_text(),
            inline=False
        )
        winners,losers=[],[]
        for b in self.bets.values():
            won,mult=evaluate(b.bt,b.bv,dice)
            lbl=blabel(b.bt,b.bv)
            if won:
                profit = b.amount * mult             # Chỉ tính phần lãi
                total_return = b.amount + profit     # Tổng nhận = Tiền gốc + Lãi
                
                u=get_user(b.user_id)
                update_money(b.user_id, u[1] + total_return)
                
                winners.append(f"{get_icon('tick', self.channel.guild, self.cog.bot)} {b.mention} · `{lbl}` · **+{total_return:,}** (x{mult})")
            else:
                losers.append(f"{get_icon('cross', self.channel.guild, self.cog.bot)} {b.mention} · `{lbl}` · **-{b.amount:,}**")
        if winners:
            e.add_field(name=f"🏆 Thắng ({len(winners)})",
                        value="\n".join(winners[:10]),inline=False)
        if losers:
            e.add_field(name=f"💸 Thua ({len(losers)})",
                        value="\n".join(losers[:10]),inline=False)
        e.set_footer(text=f"🎰 HoiNguoiHen Casino · {len(winners)} thắng / {len(losers)} thua")
        return e,df

    async def refresh(self):
        if self.message and not self.ended:
            try: await self.message.edit(embed=self._open_embed(),view=self.view)
            except discord.HTTPException: pass

    async def finish_after_delay(self):
        await asyncio.sleep(SESSION_SECONDS); await self.finish()

    async def finish(self):
        async with self.lock:
            if self.ended: return
            self.ended=True
        dice=[random.randint(1,6) for _ in range(3)]
        total=sum(dice)
        GAME_HISTORY.append({
    "tai": total >= 11,
    "chan": total % 2 == 0,
    "bao": len(set(dice)) == 1
})
        self.view.disable_all()
        if self.message:
            try: await self.message.edit(embed=self._closed_embed(),view=self.view)
            except discord.HTTPException: pass
        e,f=await self._result_embed(dice,total)
        try: await self.channel.send(embed=e,file=f)
        except discord.HTTPException:
            e.set_image(url=None); await self.channel.send(embed=e)
        self.cog.sessions.pop(self.channel.id,None)

# ─── Cog ──────────────────────────────────────────────────────────────────────
def _load_gid():
    try:
        with open("config.json", encoding="utf-8") as f:
            cfg = json.load(f)
        guilds = cfg.get("emoji_guilds", {})
        v = str(guilds.get("dice", "") or cfg.get("dice_emoji_guild_id", "")).strip()
        return int(v) if v else None
    except Exception:
        return None

class Gamble(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.sessions:dict[int,TaiXiuSession]={}
        self._gid=_load_gid()

    def get_eg(self,fallback):
        if self._gid:
            g=self.bot.get_guild(self._gid)
            if g: return g
        return fallback

    @commands.command(name="taixiu",aliases=["tx","casino"])
    async def tai_xiu(self,ctx):
        s=self.sessions.get(ctx.channel.id)
        if s and not s.ended:
            ref=f": {s.message.jump_url}" if s.message else ""
            return await ctx.send(f"🎲 Đang có phiên Tài Xỉu{ref}")
        s=TaiXiuSession(self,ctx.channel)
        self.sessions[ctx.channel.id]=s
        msg=await ctx.send(embed=s._open_embed(),view=s.view)
        s.message=msg
        self.bot.loop.create_task(s.finish_after_delay())

async def setup(bot):
    await bot.add_cog(Gamble(bot))