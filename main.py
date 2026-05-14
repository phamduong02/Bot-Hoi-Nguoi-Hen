import asyncio
import json

import aiohttp
import discord
from discord.ext import commands

from core.database import init_db
from core.combat_render_fast import (
    inject_bot,
    load_backgrounds_from_channel
)
from core.register import init_register_table
# =========================
# LOAD CONFIG
# =========================

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


# =========================
# BOT CONFIG
# =========================

intents = discord.Intents.all()
intents.message_content = True


def get_prefix(bot, message):
    return ["h", "H"]


bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    case_insensitive=True,
    help_command=None
)


# =========================
# EVENTS
# =========================
background_loaded = False 

@bot.event
async def on_ready():

    global background_loaded

    if not background_loaded:

        await bot.wait_until_ready()

        inject_bot(bot)

        await load_backgrounds_from_channel()

        background_loaded = True

    print("=" * 50)
    print(f"✅ Bot online: {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🌐 Guilds: {len(bot.guilds)}")
    print(f"👥 Users: {len(set(bot.get_all_members()))}")



# =========================
# COGS
# =========================

COGS = [
    "cogs.gacha",
    "cogs.characters",
    "cogs.combat",
    "cogs.profile",
    "cogs.menu",
    "cogs.admin",
    "cogs.gamble",
    "cogs.equip_ui",
    "cogs.daily",
    "cogs.help",
    "cogs.dex",
    "cogs.shop",  
    "cogs.weapon"
]  



async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded: {cog}")

        except Exception as e:
            print(f"❌ Failed load {cog}")
            print(e)


# =========================
# MAIN
# =========================

async def main():
    init_db()
    init_register_table()

    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


# =========================
# START
# =========================

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("🛑 Bot stopped.")

    except discord.LoginFailure:
        print("❌ Invalid bot token.")

    except aiohttp.ClientError as exc:
        print(f"❌ Network error: {exc}")

    except Exception as exc:
        print(f"❌ Unexpected error: {exc}")