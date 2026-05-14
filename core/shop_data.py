# core/shop_data.py

SHOP_ITEMS = {
    # ── GACHA CHESTS ──
    "weapon_chest": {
        "id": "1",
        "name": "Rương Vũ Khí Thần Bí",
        "type": "chest",
        "price": 2000,
        "emoji": "🎁",
        "desc": "Mở ra một vũ khí ngẫu nhiên từ Common đến Godlike."
    },
    "scroll_hero": {
        "id": "2",
        "name": "Cuộn Triệu Hồi Cao Cấp",
        "type": "chest",
        "price": 5000,
        "emoji": "📜",
        "desc": "Tặng 1 lượt chiêu mộ tướng (miễn phí phí 500 gold)."
    },

    # ── CONSUMABLES (Vật phẩm tiêu thụ) ──
    "hp_potion": {
        "id": "3",
        "name": "Bình Máu (L)",
        "type": "item",
        "price": 500,
        "emoji": "🧪",
        "desc": "Hồi phục 500 HP ngay lập tức trong trận chiến."
    },

    # ── MATERIALS (Nguyên liệu) ──
    "forge_stone": {
        "id": "4",
        "name": "Đá Cường Hóa",
        "type": "item",
        "price": 1500,
        "emoji": "💎",
        "desc": "Dùng để nâng cấp cấp độ của Vũ khí."
    }
}

def get_item_by_id(item_id):
    for key, data in SHOP_ITEMS.items():
        if data["id"] == item_id:
            return key, data
    return None, None