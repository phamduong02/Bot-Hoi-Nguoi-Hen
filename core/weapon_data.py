from __future__ import annotations

import random
from typing import Any

from core.game_data import RARITY_ORDER

# =========================
# WEAPON RARITY (GACHA)
# =========================

# Tỷ lệ mở rương vũ khí
WEAPON_RARITY_RATES: dict[str, float] = {
    "Common": 0.40,  # 40%
    "Uncommon": 0.25,  # 25%
    "Rare": 0.15,  # 15%
    "Epic": 0.10,  # 10%
    "Mythic": 0.06,  # 6%
    "Legendary": 0.03,  # 3%
    "Godlike": 0.01,  # 1%
}

# =========================
# PASSIVE DEFINITIONS
# =========================

# Passive is structured so the combat engine can apply it.
# Each weapon has exactly 1 passive for now.
PASSIVE_CATALOG: dict[str, dict[str, Any]] = {
    "lifesteal": {"name": "Hút máu"},
    "reflect": {"name": "Phản đòn"},
    "regen": {"name": "Hồi phục"},
    "ramp_magic": {"name": "Thăng tiến"},
    "mana_on_hit": {"name": "Nhạy bén"},
    "damage_bonus": {"name": "Cường hóa"},
    "justice": {"name": "Phán quyết"},
    "shield_low_hp": {"name": "Lá chắn"},
    "crit_damage": {"name": "Chí mạng tối thượng"},
    "amp_magic": {"name": "Phép thuật tối thượng"},
    "stack_spd_on_hit": {"name": "Cuồng bạo"},
    "damage_vs_high_hp": {"name": "Sát tinh"},
    "giant_growth": {"name": "Khổng lồ hóa"},
}


def describe_passive(passive: dict[str, Any]) -> str:
    """Human-readable passive text (used for embeds/UI)."""
    if not passive:
        return ""

    passive_id = passive.get("id")
    name = PASSIVE_CATALOG.get(passive_id, {}).get("name", passive_id or "Passive")

    if passive_id == "lifesteal":
        return f"{name}: Hồi {int(passive.get('rate', 0) * 100)}% sát thương gây ra thành HP."
    if passive_id == "reflect":
        return f"{name}: Phản lại {int(passive.get('rate', 0) * 100)}% sát thương nhận vào."
    if passive_id == "regen":
        return f"{name}: Hồi {int(passive.get('rate', 0) * 100)}% HP tối đa mỗi lượt."
    if passive_id == "ramp_magic":
        return f"{name}: Tăng +{int(passive.get('amount', 0))} ATK phép mỗi lượt."
    if passive_id == "mana_on_hit":
        return f"{name}: Đòn đánh thường hồi +{int(passive.get('amount', 0))} mana."
    if passive_id == "damage_bonus":
        return f"{name}: Tăng +{int(passive.get('bonus', 0) * 100)}% sát thương."
    if passive_id == "justice":
        dmg = int(passive.get("damage_bonus", 0) * 100)
        ls = int(passive.get("lifesteal_bonus", 0) * 100)
        return f"{name}: Mỗi trận nhận 1 hiệu ứng: +{dmg}% sát thương hoặc +{ls}% hút máu."
    if passive_id == "shield_low_hp":
        threshold = int(passive.get("threshold", 0) * 100)
        ratio = int(passive.get("shield_ratio", 0) * 100)
        return f"{name}: Khi dưới {threshold}% HP, nhận khiên bằng {ratio}% HP tối đa (1 lần/trận)."
    if passive_id == "crit_damage":
        bonus = float(passive.get("bonus", 0.0))
        return f"{name}: Sát thương chí mạng +{int(bonus * 100)}%."
    if passive_id == "amp_magic":
        return f"{name}: Tăng tổng ATK phép +{int(passive.get('rate', 0) * 100)}%."
    if passive_id == "stack_spd_on_hit":
        return f"{name}: Mỗi đòn đánh tăng +{int(passive.get('amount', 0))} SPD (cộng dồn)."
    if passive_id == "damage_vs_high_hp":
        threshold_hp = int(passive.get("threshold_hp", 0))
        bonus = int(passive.get("bonus", 0) * 100)
        return f"{name}: Gây thêm +{bonus}% sát thương lên mục tiêu có ≥ {threshold_hp} HP tối đa."
    if passive_id == "giant_growth":
        atk = int(passive.get("atk", 0))
        defense = int(passive.get("def", 0))
        stacks = int(passive.get("max_stacks", 0))
        bonus_hp = int(passive.get("bonus_hp", 0))
        return (
            f"{name}: Mỗi lượt tăng +{atk} ATK và +{defense} DEF (tối đa {stacks} lần). "
            f"Đủ cộng dồn nhận thêm +{bonus_hp} HP."
        )

    return str(passive.get("text") or name)


# =========================
# WEAPON DATA
# =========================

# Kho vũ khí đồng bộ với Emoji Server
WEAPONS: dict[str, dict[str, Any]] = {
    # ── COMMON ──
    "kiem_sung": {
        "name": "Kiếm Súng Hextech",
        "rarity": "Common",
        "emoji": "kiemsung",
        "stats": {"atk_phys": 15, "atk_magic": 15},
        "passive": {"id": "lifesteal", "rate": 0.10},
    },
    "chiu_doan_con": {
        "name": "Chùy Đoản Côn",
        "rarity": "Common",
        "emoji": "chiudoancon",
        "stats": {"atk_phys": 20, "spd": 5},
        "passive": {"id": "damage_bonus", "bonus": 0.05},
    },
    # ── UNCOMMON ──
    "giap_gai": {
        "name": "Giáp Gai",
        "rarity": "Uncommon",
        "emoji": "giapgai",
        "stats": {"def_phys": 50, "hp": 200},
        "passive": {"id": "reflect", "rate": 0.15},
    },
    "giap_mau": {
        "name": "Giáp Máu Warmog",
        "rarity": "Uncommon",
        "emoji": "giapmau",
        "stats": {"hp": 1000},
        "passive": {"id": "regen", "rate": 0.01},
    },
    "aochoanglua": {
        "name": "Áo Choàng Lửa",
        "rarity": "Uncommon",
        "emoji": "aochoanglua",
        "stats": {"hp": 300, "def_phys": 30},
        "passive": {"id": "regen", "rate": 0.008},
    },
    "loi_the_ho_ve": {
        "name": "Lời Thề Hộ Vệ",
        "rarity": "Uncommon",
        "emoji": "loithehove",
        "stats": {"hp": 250, "def_phys": 20, "def_magic": 20},
        "passive": {"id": "reflect", "rate": 0.08},
    },
    "aochoangthuyngan": {
        "name": "Áo Choàng Thủy Ngân",
        "rarity": "Uncommon",
        "emoji": "aochoangthuyngan",
        "stats": {"def_magic": 45, "spd": 10},
        "passive": {"id": "shield_low_hp", "threshold": 0.45, "shield_ratio": 0.18},
    },
    "buado": {
        "name": "Bùa Đỏ",
        "rarity": "Uncommon",
        "emoji": "buado",
        "stats": {"atk_phys": 22, "hp": 120},
        "passive": {"id": "damage_bonus", "bonus": 0.06},
    },
    # ── RARE ──
    "quyen_truong_thien_than": {
        "name": "Quyền Trượng Thiên Thần",
        "rarity": "Rare",
        "emoji": "quyentruongthienthan",
        "stats": {"atk_magic": 40, "hp": 150},
        "passive": {"id": "ramp_magic", "amount": 5},
    },
    "shojin": {
        "name": "Thương Shojin",
        "rarity": "Rare",
        "emoji": "shojin",
        "stats": {"atk_phys": 20, "atk_magic": 20, "spd": 15},
        "passive": {"id": "mana_on_hit", "amount": 5},
    },
    "noset": {
        "name": "Nỏ Sét",
        "rarity": "Rare",
        "emoji": "noset",
        "stats": {"atk_magic": 25, "spd": 25},
        "passive": {"id": "mana_on_hit", "amount": 8},
    },
    "nanh_nashor": {
        "name": "Nanh Nashor",
        "rarity": "Rare",
        "emoji": "nanhnashor",
        "stats": {"atk_magic": 35, "spd": 20},
        "passive": {"id": "ramp_magic", "amount": 7},
    },
    "giap_tam_linh": {
        "name": "Giáp Tâm Linh",
        "rarity": "Rare",
        "emoji": "giaptamlinh",
        "stats": {"def_magic": 60, "hp": 300},
        "passive": {"id": "regen", "rate": 0.012},
    },
    "mubomman": {
        "name": "Mũ Bom Man",
        "rarity": "Rare",
        "emoji": "mubomman",
        "stats": {"atk_magic": 28, "crit": 10, "spd": 12},
        "passive": {"id": "mana_on_hit", "amount": 6},
    },
    "giapvainguyetthan": {
        "name": "Giáp Vầng Nguyệt Thần",
        "rarity": "Rare",
        "emoji": "giapvainguyetthan",
        "stats": {"hp": 350, "def_magic": 45},
        "passive": {"id": "regen", "rate": 0.014},
    },
    "quythu": {
        "name": "Quỷ Thư",
        "rarity": "Rare",
        "emoji": "quythu",
        "stats": {"atk_magic": 45, "hp": 220},
        "passive": {"id": "damage_bonus", "bonus": 0.10},
    },
    # ── EPIC ──
    "ban_tay_cong_ly": {
        "name": "Bàn Tay Công Lý",
        "rarity": "Epic",
        "emoji": "bantaycongly",
        "stats": {"atk_phys": 30, "atk_magic": 30, "crit": 15},
        "passive": {"id": "justice", "damage_bonus": 0.20, "lifesteal_bonus": 0.20},
    },
    "huyet_kiem": {
        "name": "Huyết Kiếm",
        "rarity": "Epic",
        "emoji": "huyetkiem",
        "stats": {"atk_phys": 45, "def_magic": 20},
        "passive": {"id": "shield_low_hp", "threshold": 0.40, "shield_ratio": 0.25},
    },
    "gang_bao_thach": {
        "name": "Găng Bảo Thạch",
        "rarity": "Epic",
        "emoji": "gangbaothach",
        "stats": {"atk_magic": 35, "crit": 20},
        "passive": {"id": "crit_damage", "bonus": 0.25},
    },
    "mong_vuot_sterak": {
        "name": "Móng Vuốt Sterak",
        "rarity": "Epic",
        "emoji": "mongvuotsterak",
        "stats": {"hp": 400, "atk_phys": 25},
        "passive": {"id": "shield_low_hp", "threshold": 0.45, "shield_ratio": 0.30},
    },
    "aochoangbongtoi": {
        "name": "Áo Choàng Bóng Tối",
        "rarity": "Epic",
        "emoji": "aochoangbongtoi",
        "stats": {"def_phys": 35, "def_magic": 35, "spd": 10},
        "passive": {"id": "shield_low_hp", "threshold": 0.40, "shield_ratio": 0.22},
    },
    "thinhno": {
        "name": "Thịnh Nộ",
        "rarity": "Epic",
        "emoji": "thinhno",
        "stats": {"atk_phys": 35, "spd": 20, "def_phys": 20},
        "passive": {"id": "stack_spd_on_hit", "amount": 3},
    },
    "thutuongthachgiap": {
        "name": "Thú Tượng Thạch Giáp",
        "rarity": "Epic",
        "emoji": "thutuongthachgiap",
        "stats": {"hp": 350, "def_phys": 55, "def_magic": 55},
        "passive": {"id": "shield_low_hp", "threshold": 0.38, "shield_ratio": 0.28},
    },
    # ── MYTHIC ──
    "vo_cuc_kiem": {
        "name": "Vô Cực Kiếm",
        "rarity": "Mythic",
        "emoji": "vocuckiem",
        "stats": {"atk_phys": 80, "crit": 25},
        "passive": {"id": "crit_damage", "bonus": 0.50},
    },
    "mu_phu_thuy": {
        "name": "Mũ Phù Thủy Rabadon",
        "rarity": "Mythic",
        "emoji": "muphuthuy",
        "stats": {"atk_magic": 100},
        "passive": {"id": "amp_magic", "rate": 0.30},
    },
    "quyen_truong_hu_vo": {
        "name": "Quyền Trượng Hư Vô",
        "rarity": "Mythic",
        "emoji": "quyentruonghuvo",
        "stats": {"atk_magic": 80},
        "passive": {"id": "damage_bonus", "bonus": 0.15},
    },
    "bua_xanh": {
        "name": "Bùa Xanh",
        "rarity": "Mythic",
        "emoji": "buaxanh",
        "stats": {"atk_magic": 50, "spd": 15},
        "passive": {"id": "mana_on_hit", "amount": 12},
    },
    "traitim": {
        "name": "Trái Tim",
        "rarity": "Mythic",
        "emoji": "traitim",
        "stats": {"hp": 800, "def_phys": 35, "def_magic": 35},
        "passive": {"id": "regen", "rate": 0.02},
    },
    # ── LEGENDARY ──
    "cuong_dao": {
        "name": "Cuồng Đao Guinsoo",
        "rarity": "Legendary",
        "emoji": "cuongdao",
        "stats": {"atk_phys": 40, "atk_magic": 40, "spd": 30},
        "passive": {"id": "stack_spd_on_hit", "amount": 5},
    },
    "diet_khong_lo": {
        "name": "Diệt Khổng Lồ",
        "rarity": "Legendary",
        "emoji": "dietkhonglo",
        "stats": {"atk_phys": 50, "spd": 20},
        "passive": {"id": "damage_vs_high_hp", "threshold_hp": 2000, "bonus": 0.20},
    },
    "cung_xanh": {
        "name": "Cung Xanh",
        "rarity": "Legendary",
        "emoji": "cungxanh",
        "stats": {"atk_phys": 45, "crit": 20},
        "passive": {"id": "damage_bonus", "bonus": 0.18},
    },
    "vuot_rong": {
        "name": "Vuốt Rồng",
        "rarity": "Legendary",
        "emoji": "vuotrong",
        "stats": {"def_magic": 80, "hp": 250},
        "passive": {"id": "reflect", "rate": 0.12},
    },
    "kiemthuthan": {
        "name": "Kiếm Thú Thần",
        "rarity": "Legendary",
        "emoji": "kiemthuthan",
        "stats": {"atk_phys": 65, "crit": 18, "spd": 10},
        "passive": {"id": "crit_damage", "bonus": 0.35},
    },
    # ── GODLIKE ──
    "quyen_nang": {
        "name": "Quyền Năng Khổng Lồ",
        "rarity": "Godlike",
        "emoji": "quyennang",
        "stats": {"atk_phys": 50, "def_phys": 50, "def_magic": 50},
        "passive": {"id": "giant_growth", "atk": 15, "def": 15, "max_stacks": 5, "bonus_hp": 500},
    },
    "vuongmienhoanggia": {
        "name": "Vương Miện Hoàng Gia",
        "rarity": "Godlike",
        "emoji": "vuongmienhoanggia",
        "stats": {"hp": 500, "def_magic": 70, "atk_magic": 40},
        "passive": {"id": "justice", "damage_bonus": 0.25, "lifesteal_bonus": 0.25},
    },
}


def _normalize_rates(rates: dict[str, float]) -> dict[str, float]:
    dist = {rarity: max(0.0, float(chance)) for rarity, chance in rates.items()}
    total = sum(dist.values())
    if total <= 0:
        return {"Common": 1.0}

    if total < 1.0:
        dist["Common"] = dist.get("Common", 0.0) + (1.0 - total)
        total = 1.0
    elif total > 1.0:
        for key in list(dist.keys()):
            dist[key] = dist[key] / total
        total = 1.0

    normalized: dict[str, float] = {}
    for rarity in RARITY_ORDER:
        normalized[rarity] = dist.get(rarity, 0.0)
    return normalized


def roll_weapon_rarity(rng=None) -> tuple[str, int]:
    """Roll rarity for weapon chest/shop. Returns (rarity, roll_percent[1..100])."""
    random_source = rng or random
    dist = _normalize_rates(WEAPON_RARITY_RATES)

    r = float(random_source.random())
    cumulative = 0.0
    chosen = "Common"
    for rarity in RARITY_ORDER:
        chance = dist.get(rarity, 0.0)
        cumulative += chance
        if r <= cumulative:
            chosen = rarity
            break

    roll_percent = max(1, min(100, int(r * 100) + 1))
    return chosen, roll_percent


def _pick_weapon_code_by_rarity(rarity: str, rng=None) -> str:
    random_source = rng or random
    pool = [code for code, data in WEAPONS.items() if data.get("rarity") == rarity]
    if not pool:
        pool = list(WEAPONS.keys())
    return random_source.choice(pool)


def _roll_stats(
    base_stats: dict[str, int],
    rng=None,
    spread: tuple[float, float] = (0.8, 1.25),
) -> dict[str, int]:
    random_source = rng or random
    low, high = spread
    rolled: dict[str, int] = {}
    for stat_name, stat_value in (base_stats or {}).items():
        rolled[stat_name] = int(stat_value * float(random_source.uniform(low, high)))
    return rolled


def generate_weapon_instance(
    rng=None,
    rarity: str | None = None,
    weapon_code: str | None = None,
    stat_spread: tuple[float, float] = (0.8, 1.25),
) -> dict[str, Any]:
    """
    Generate a weapon instance for shop/chest/drop.
    - If rarity is None: roll rarity + return rarity_roll (1..100)
    - If weapon_code is None: pick by rarity pool
    - Stats are rolled from base stats (spread)
    """
    random_source = rng or random

    if rarity is None:
        rarity, rarity_roll = roll_weapon_rarity(random_source)
    else:
        rarity_roll = 0

    if weapon_code is None:
        weapon_code = _pick_weapon_code_by_rarity(rarity, random_source)

    w_def = WEAPONS.get(weapon_code) or {}
    stats = _roll_stats(w_def.get("stats", {}), random_source, spread=stat_spread)

    passive = dict(w_def.get("passive") or {})
    passive_text = describe_passive(passive) if passive else ""

    return {
        "code": weapon_code,
        "rarity": rarity,
        "rarity_roll": rarity_roll,
        "name": w_def.get("name", weapon_code),
        "emoji": w_def.get("emoji", ""),
        "stats": stats,
        "passive": passive,
        "passive_text": passive_text,
    }
