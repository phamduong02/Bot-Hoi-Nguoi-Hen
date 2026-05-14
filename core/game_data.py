# Cập nhật lại thứ tự độ hiếm
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Mythic", "Legendary", "Godlike"]
RARITY = {
    "Common": 0.45,
    "Uncommon": 0.25,
    "Rare": 0.15,
    "Epic": 0.08,
    "Mythic": 0.015,        # 1.5% - Dễ ra hơn Legendary
    "Legendary": 0.001,    # 0.1% - Hiếm hơn Mythic
    "Godlike": 0.0001       # 0.01% - Cao nhất
}
MULTIPLIER = {
    "Common": 1.0,
    "Uncommon": 1.1,
    "Rare": 1.25,
    "Epic": 1.5,
    "Mythic": 2.0,
    "Legendary": 2.5,
    "Godlike": 3.0
}
# (Bên dưới là danh sách CHARACTERS của bạn)
CHARACTERS = [
    # ── Common (8) ──
# COMMON
    {"name": "Cá Trê Chúa", "class": "Tank", "rarity": "Common", "emoji": "tahmkench"},
    {"name": "Rồng Con Cay Cú", "class": "ADC", "rarity": "Common", "emoji": "smolder"},
    {"name": "Chị Đâm Thuê", "class": "Warrior", "rarity": "Common", "emoji": "fiora"},
    {"name": "Cảnh Sát Piltover", "class": "ADC", "rarity": "Common", "emoji": "caitlyn"},
    {"name": "Boy Đeo Găng", "class": "ADC", "rarity": "Common", "emoji": "ez"},
    {"name": "Chiến Binh Wifi", "class": "Warrior", "rarity": "Common", "emoji": "pantheon"},
    {"name": "Thằng Bé Tuyết", "class": "Tank", "rarity": "Common", "emoji": "nunu"},
    {"name": "4 Viên Là Ngủ", "class": "ADC", "rarity": "Common", "emoji": "jhin"},
    # NEW
    {"name": "Chồn Lùi", "class": "Mage", "rarity": "Common", "emoji": "teemo"},
    {"name": "Hai Nòng Bốc Đầu", "class": "ADC", "rarity": "Common", "emoji": "graves"},
    {"name": "Máy Chém Noxus", "class": "Warrior", "rarity": "Common", "emoji": "darius"},
    # UNCOMMON
    {"name": "Ninja Chống Đạn", "class": "Tank", "rarity": "Uncommon", "emoji": "shen"},
    {"name": "Đèn Pin Thần", "class": "Warrior", "rarity": "Uncommon", "emoji": "jax"},
    {"name": "Bé Gấu Đốt Nhà", "class": "Mage", "rarity": "Uncommon", "emoji": "annie"},
    {"name": "2 Kiếm 1 Não", "class": "Assassin", "rarity": "Uncommon", "emoji": "yone"},
    {"name": "Bọ Nhảy Bụi", "class": "Assassin", "rarity": "Uncommon", "emoji": "khazix"},
    {"name": "Mèo Rừng", "class": "Assassin", "rarity": "Uncommon", "emoji": "rengar"},
    {"name": "Quay Tay Bất Tử", "class": "Warrior", "rarity": "Uncommon", "emoji": "tryn"},
    {"name": "Rắn 3 Đầu", "class": "Tank", "rarity": "Uncommon", "emoji": "3ron"},
    # NEW
    {"name": "Robocon", "class": "Tank", "rarity": "Uncommon", "emoji": "blitzcrank"},
    {"name": "Tia Điện ADHD", "class": "ADC", "rarity": "Uncommon", "emoji": "zeri"},
    {"name": "Thầy Chùa Mù", "class": "Warrior", "rarity": "Uncommon", "emoji": "leesin"},
    # RARE
    {"name": "Sứ Giả Đao Đần", "class": "Tank", "rarity": "Rare", "emoji": "sugiakn"},
    {"name": "Cung Thủ Freljord", "class": "ADC", "rarity": "Rare", "emoji": "ashe"},
    {"name": "Namichan", "class": "Mage", "rarity": "Rare", "emoji": "nami"},
    {"name": "Bà Trùm Hai Súng", "class": "ADC", "rarity": "Rare", "emoji": "mis4"},
    {"name": "Hồ Ly Trap", "class": "Mage", "rarity": "Rare", "emoji": "ahri"},
    {"name": "AFK", "class": "Mage", "rarity": "Rare", "emoji": "yuumi"},
    {"name": "Tắc Kè Hoa", "class": "Mage", "rarity": "Rare", "emoji": "neeko"},
    {"name": "Pháp Sư Hóa Cóc", "class": "Mage", "rarity": "Rare", "emoji": "lulu"},
    {"name": "Ác Quỷ Void", "class": "ADC", "rarity": "Rare", "emoji": "kaisa"},
    {"name": "Thiên Thần Sa Ngã", "class": "Mage", "rarity": "Rare", "emoji": "morgana"},
    # EPIC
    {"name": "Xe Cứu Thương", "class": "Mage", "rarity": "Epic", "emoji": "soraka"},
    {"name": "Búp Bê Cầm Kéo", "class": "Warrior", "rarity": "Epic", "emoji": "gwen"},
    {"name": "Thỏ Ma Thuật", "class": "Mage", "rarity": "Epic", "emoji": "aurora"},
    {"name": "Máy Xay Demacia", "class": "Warrior", "rarity": "Epic", "emoji": "garen"},
    {"name": "Đèn Pin Laser", "class": "Mage", "rarity": "Epic", "emoji": "lux"},
    {"name": "Bé Điên Bắn Cá", "class": "ADC", "rarity": "Epic", "emoji": "jinx"},
    {"name": "Mặt Trời Biết Đi", "class": "Tank", "rarity": "Epic", "emoji": "leona"},
    {"name": "Thiên Sứ Phán Xét", "class": "Warrior", "rarity": "Epic", "emoji": "kayle"},
    {"name": "Cục Đá Biết Bay", "class": "Tank", "rarity": "Epic", "emoji": "malphite", "emoji_aliases": ("manphite",)},
    # MYTHIC
    {"name": "taolabomay", "class": "Warrior", "rarity": "Mythic", "emoji": "sett"},
    {"name": "DJ Pentakill", "class": "Mage", "rarity": "Mythic", "emoji": "sona"},
    {"name": "Hasagi Spam", "class": "Warrior", "rarity": "Mythic", "emoji": "daxua"},
    {"name": "Cậu Bé Thời Gian", "class": "Assassin", "rarity": "Mythic", "emoji": "ekko"},
    {"name": "OK.", "class": "Tank", "rarity": "Mythic", "emoji": "rammus"},
    {"name": "Xác Ướp Khóc Thuê", "class": "Tank", "rarity": "Mythic", "emoji": "amumu"},
    {"name": "Chúa Tể Bóng Tối", "class": "Assassin", "rarity": "Mythic", "emoji": "zed"},
    {"name": "Con Cá Đánh Người", "class": "Assassin", "rarity": "Mythic", "emoji": "fizz"},
    {"name": "Hoàng Đế", "class": "Mage", "rarity": "Mythic", "emoji": "azir"},
    # LEGENDARY
    {"name": "Hồ Ly Idol", "class": "Mage", "rarity": "Legendary", "emoji": "ahri1"},
    # GODLIKE
    {"name": "Cửu Vĩ Hoa Linh", "class": "Mage", "rarity": "Godlike", "emoji": "ahrihoalinh"},
]
