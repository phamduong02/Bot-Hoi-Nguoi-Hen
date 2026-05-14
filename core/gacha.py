import random
from core.game_data import RARITY, MULTIPLIER, CHARACTERS
from core.database import add_character

def roll_rarity():
    # RARITY được hiểu là xác suất (0..1).
    # Nếu tổng < 1 → phần dư sẽ được tính vào Common (tránh bug dồn về rarity cuối).
    # Nếu tổng > 1 → tự normalize về 1.
    if not RARITY:
        return "Common"

    dist = {rarity: max(0.0, float(chance)) for rarity, chance in RARITY.items()}
    total = sum(dist.values())

    if total <= 0:
        return next(iter(dist))

    if total < 1.0:
        remainder = 1.0 - total
        if "Common" in dist:
            dist["Common"] += remainder
        else:
            first_key = next(iter(dist))
            dist[first_key] += remainder
        total = 1.0
    elif total > 1.0:
        for key in dist:
            dist[key] /= total
        total = 1.0

    r = random.random() * total
    cumulative = 0.0
    last = next(reversed(dist))
    for rarity, chance in dist.items():
        cumulative += chance
        if r <= cumulative:
            return rarity

    return last

# ĐÃ CÂN BẰNG LẠI CHỈ SỐ THEO MỨC MÁU 700+
# Đảm bảo CLASS_STATS của bạn có đủ 5 hệ này nhé:
# Đã giảm ATK/MATK xuống khoảng 50% để đánh thường yếu đi
CLASS_STATS = {
    "Tank": {
        "hp": (900, 1200),
        "atk_phys": (40, 70),       # Giảm
        "atk_magic": (10, 30),      # Giảm
        "def_phys": (250, 400),
        "def_magic": (200, 300),
    },
    "Mage": {
        "hp": (700, 850),
        "atk_phys": (15, 30),       # Giảm
        "atk_magic": (120, 200),    # Giảm
        "def_phys": (100, 150),
        "def_magic": (150, 250),
    },
    "Warrior": {
        "hp": (800, 1050),
        "atk_phys": (90, 140),      # Giảm
        "atk_magic": (15, 30),      # Giảm
        "def_phys": (150, 220),
        "def_magic": (100, 150),
    },
    "Assassin": {
        "hp": (700, 800),
        "atk_phys": (120, 180),     # Giảm
        "atk_magic": (15, 30),      # Giảm
        "def_phys": (100, 150),
        "def_magic": (80, 130),
    },
    "ADC": {
        "hp": (650, 750),           
        "atk_phys": (150, 220),     # Giảm (Vẫn là cao nhất)
        "atk_magic": (10, 20),      # Giảm
        "def_phys": (80, 120),
        "def_magic": (80, 120),
    }
}

def generate_stats(char_name, cls, rarity):
    mult = MULTIPLIER[rarity]
    base = CLASS_STATS.get(cls)

    if not base:
        return None

    rng = random.Random(char_name)

    stats = {
        stat: int(rng.randint(v[0], v[1]) * mult)
        for stat, v in base.items()
    }

    stats["spd"] = int(rng.randint(20, 50) * mult)
    stats["crit"] = int(rng.randint(5, 20) * mult)
    
    # ADC được cộng thêm tốc độ
    if cls == "ADC":
        stats["spd"] = int(rng.randint(45, 65) * mult)

    if stats["crit"] > 100:
        stats["crit"] = 100

    return stats

def summon_character(user_id):
    rarity = roll_rarity()
    # Tìm tướng đúng độ hiếm
    candidates = [char for char in CHARACTERS if char.get("rarity") == rarity]
    
    # Nếu độ hiếm đó chưa có tướng nào (ví dụ Godlike chưa có tướng)
    if not candidates:
        # Quay lại chọn một tướng bất kỳ trong danh sách để không bị lỗi
        char = random.choice(CHARACTERS)
        # Lấy luôn độ hiếm gốc của con tướng đó để tính stats cho chuẩn
        rarity = char["rarity"] 
    else:
        char = random.choice(candidates)
    
    # Tạo chỉ số dựa trên độ hiếm cuối cùng
    stats = generate_stats(char["name"], char["class"], rarity)

    # Lưu vào database
    from core.database import add_character
    add_character(user_id, char["name"], char["class"], rarity, stats)

    return {
        "name": char["name"],
        "class": char["class"],
        "rarity": rarity,
        "stats": stats
    }
