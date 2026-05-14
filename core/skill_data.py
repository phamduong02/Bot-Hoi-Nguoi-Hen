from __future__ import annotations

from typing import Any

from core.game_data import CHARACTERS


Skill = dict[str, Any]


# One skill per character (for now).
# Keys MUST match `core.game_data.CHARACTERS[i]["name"]`.
SKILLS = {

    # ═════════════════ COMMON ═════════════════

    "Cá Trê Chúa": {
        "name": "Nuốt Chửng",
        "cooldown": 3,
        "tags": ["Tank", "Control"],
        "description": "Nuốt mục tiêu, hồi HP và tạo khiên cho đồng minh thấp máu nhất.",
    },

    "Rồng Con Cay Cú": {
        "name": "Hỏa Long Gầm",
        "cooldown": 2,
        "tags": ["ADC", "Damage"],
        "description": "Phun lửa gây sát thương và tăng CRIT cho bản thân.",
    },

    "Chị Đâm Thuê": {
        "name": "Phản Kiếm",
        "cooldown": 3,
        "tags": ["Warrior", "Counter"],
        "description": "Đỡ đòn và phản công bằng sát thương cực mạnh.",
    },

    "Cảnh Sát Piltover": {
        "name": "Bắn Tỉa",
        "cooldown": 3,
        "tags": ["ADC", "Burst"],
        "description": "Ngắm bắn chính xác, xuyên DEF mục tiêu.",
    },

    "Boy Đeo Găng": {
        "name": "Cung Ánh Sáng",
        "cooldown": 3,
        "tags": ["ADC", "Magic"],
        "description": "Bắn năng lượng gây sát thương phép.",
    },

    "Chiến Binh Wifi": {
        "name": "Thiên Thạch Rơi",
        "cooldown": 4,
        "tags": ["Warrior", "AoE"],
        "description": "Nhảy từ trời xuống gây sát thương diện rộng.",
    },

    "Thằng Bé Tuyết": {
        "name": "Bão Tuyết",
        "cooldown": 4,
        "tags": ["Tank", "AoE"],
        "description": "Đóng băng kẻ địch và hồi máu đồng minh.",
    },

    "4 Viên Là Ngủ": {
        "name": "Phát Đạn Cuối",
        "cooldown": 4,
        "tags": ["ADC", "Execute"],
        "description": "Viên đạn cuối gây sát thương cực lớn.",
    },

    "Chồn Lùi": {
        "name": "Nấm Độc",
        "cooldown": 3,
        "tags": ["Mage", "Poison"],
        "description": "Rải nấm độc gây sát thương theo thời gian.",
    },

    "Hai Nòng Bốc Đầu": {
        "name": "Đạn Nổ",
        "cooldown": 3,
        "tags": ["ADC", "Burst"],
        "description": "Bắn phát đạn cực mạnh gây nổ diện rộng.",
    },

    "Máy Chém Noxus": {
        "name": "Tử Hình",
        "cooldown": 4,
        "tags": ["Warrior", "Execute"],
        "description": "Chém cực mạnh lên mục tiêu thấp máu.",
    },


    # ═════════════════ UNCOMMON ═════════════════

    "Ninja Chống Đạn": {
        "name": "Bảo Hộ",
        "cooldown": 4,
        "tags": ["Tank", "Support"],
        "description": "Tạo khiên bảo vệ đồng đội.",
    },

    "Đèn Pin Thần": {
        "name": "Phản Công",
        "cooldown": 3,
        "tags": ["Warrior", "Control"],
        "description": "Né đòn và phản stun mục tiêu.",
    },

    "Bé Gấu Đốt Nhà": {
        "name": "Triệu Hồi Gấu",
        "cooldown": 4,
        "tags": ["Mage", "Burst"],
        "description": "Gọi gấu lửa gây sát thương diện rộng.",
    },

    "2 Kiếm 1 Não": {
        "name": "Chém Linh Hồn",
        "cooldown": 4,
        "tags": ["Assassin", "Burst"],
        "description": "Lao tới chém gây giảm DEF.",
    },

    "Bọ Nhảy Bụi": {
        "name": "Săn Mồi",
        "cooldown": 2,
        "tags": ["Assassin", "Burst"],
        "description": "Tấn công cực mạnh mục tiêu đơn.",
    },

    "Mèo Rừng": {
        "name": "Vồ Mồi",
        "cooldown": 4,
        "tags": ["Assassin", "Crit"],
        "description": "Tăng tốc độ và CRIT.",
    },

    "Quay Tay Bất Tử": {
        "name": "Bất Tử",
        "cooldown": 5,
        "tags": ["Warrior", "Survival"],
        "description": "Không thể chết trong thời gian ngắn.",
    },

    "Rắn 3 Đầu": {
        "name": "Cuồng Nộ Hư Không",
        "cooldown": 4,
        "tags": ["Tank", "Boss"],
        "description": "Giảm DEF toàn đội địch.",
    },

    "Robocon": {
        "name": "Bàn Tay Hỏa Tiễn",
        "cooldown": 4,
        "tags": ["Tank", "Control"],
        "description": "Kéo và stun mục tiêu.",
    },

    "Tia Điện ADHD": {
        "name": "Sét Giật",
        "cooldown": 4,
        "tags": ["ADC", "Mobility"],
        "description": "Gây sát thương và tăng SPD.",
    },

    "Thầy Chùa Mù": {
        "name": "Cước Rồng",
        "cooldown": 4,
        "tags": ["Warrior", "Burst"],
        "description": "Đá bay mục tiêu gây stun.",
    },


    # ═════════════════ RARE ═════════════════

    "Sứ Giả Đao Đần": {
        "name": "Húc Đầu",
        "cooldown": 4,
        "tags": ["Tank", "Damage"],
        "description": "Húc cực mạnh làm choáng.",
    },

    "Cung Thủ Freljord": {
        "name": "Đại Băng Tiễn",
        "cooldown": 4,
        "tags": ["ADC", "Control"],
        "description": "Làm choáng và giảm SPD.",
    },

    "Namichan": {
        "name": "Sóng Thần",
        "cooldown": 4,
        "tags": ["Mage", "Support"],
        "description": "Hồi máu cho đồng minh.",
    },

    "Bà Trùm Hai Súng": {
        "name": "Mưa Đạn",
        "cooldown": 4,
        "tags": ["ADC", "AoE"],
        "description": "Xả đạn toàn bộ đội hình địch.",
    },

    "Hồ Ly Trap": {
        "name": "Hồ Hỏa",
        "cooldown": 3,
        "tags": ["Mage", "Burst"],
        "description": "Lướt và gây sát thương phép.",
    },

    "AFK": {
        "name": "Ngủ Trên Vai",
        "cooldown": 4,
        "tags": ["Mage", "Support"],
        "description": "Hồi máu đồng minh thấp nhất.",
    },

    "Tắc Kè Hoa": {
        "name": "Nở Hoa",
        "cooldown": 4,
        "tags": ["Mage", "Control"],
        "description": "Làm choáng ngẫu nhiên.",
    },

    "Pháp Sư Hóa Cóc": {
        "name": "Khổng Lồ Hóa",
        "cooldown": 4,
        "tags": ["Mage", "Support"],
        "description": "Buff HP và DEF cho đồng minh.",
    },


    # ═════════════════ EPIC ═════════════════

    "Xe Cứu Thương": {
        "name": "Điều Ước",
        "cooldown": 5,
        "tags": ["Mage", "Healer"],
        "description": "Hồi máu toàn đội.",
    },

    "Búp Bê Cầm Kéo": {
        "name": "Khâu Vá",
        "cooldown": 3,
        "tags": ["Warrior", "Damage"],
        "description": "Chém liên tục giảm DEF.",
    },

    "Thỏ Ma Thuật": {
        "name": "Không Gian Dị Giới",
        "cooldown": 4,
        "tags": ["Mage", "Trick"],
        "description": "Buff SPD cho cả đội.",
    },

    "Máy Xay Demacia": {
        "name": "Công Lý",
        "cooldown": 4,
        "tags": ["Warrior", "Execute"],
        "description": "Chém kết liễu mục tiêu thấp máu.",
    },

    "Đèn Pin Laser": {
        "name": "Laser Tử Thần",
        "cooldown": 4,
        "tags": ["Mage", "Burst"],
        "description": "Bắn laser sát thương cực mạnh.",
    },

    "Bé Điên Bắn Cá": {
        "name": "Tên Lửa Cá Heo",
        "cooldown": 4,
        "tags": ["ADC", "Burst"],
        "description": "Tên lửa gây sát thương khổng lồ.",
    },

    "Mặt Trời Biết Đi": {
        "name": "Thái Dương",
        "cooldown": 4,
        "tags": ["Tank", "Control"],
        "description": "Làm choáng toàn bộ đội địch.",
    },


    # ═════════════════ MYTHIC ═════════════════

    "taolabomay": {
        "name": "Đấm Phát Chết Luôn",
        "cooldown": 4,
        "tags": ["Warrior", "Burst"],
        "description": "Đấm cực mạnh giảm DEF.",
    },

    "DJ Pentakill": {
        "name": "Drop The Beat",
        "cooldown": 4,
        "tags": ["Mage", "Support"],
        "description": "Buff và hồi máu đồng đội.",
    },

    "Hasagi Spam": {
        "name": "Hasagi",
        "cooldown": 4,
        "tags": ["Warrior", "Crit"],
        "description": "Tăng CRIT và chém liên tục.",
    },

    "Cậu Bé Thời Gian": {
        "name": "Quay Ngược",
        "cooldown": 5,
        "tags": ["Assassin", "Reset"],
        "description": "Hồi máu và reset vị trí.",
    },

    "OK.": {
        "name": "Phản Giáp",
        "cooldown": 3,
        "tags": ["Tank", "Reflect"],
        "description": "Phản lại sát thương nhận vào.",
    },

    "Xác Ướp Khóc Thuê": {
        "name": "Lời Nguyền",
        "cooldown": 5,
        "tags": ["Tank", "AoE"],
        "description": "Stun toàn bộ đội địch.",
    },

    "Chúa Tể Bóng Tối": {
        "name": "Dấu Ấn Tử Thần",
        "cooldown": 4,
        "tags": ["Assassin", "Burst"],
        "description": "Đặt dấu ấn gây nổ sát thương.",
    },

    "Con Cá Đánh Người": {
        "name": "Cá Mập Cắn",
        "cooldown": 4,
        "tags": ["Assassin", "Burst"],
        "description": "Triệu hồi cá mập cắn mục tiêu.",
    },

    "Hoàng Đế": {
        "name": "Bão Cát",
        "cooldown": 5,
        "tags": ["Mage", "AoE"],
        "description": "Tạo tường cát đẩy lùi kẻ địch.",
    },


    # ═════════════════ LEGENDARY ═════════════════

    "Hồ Ly Idol": {
        "name": "Hồ Hỏa Idol",
        "cooldown": 5,
        "tags": ["Mage", "Burst"],
        "description": "Gây sát thương phép cực lớn.",
    },


    # ═════════════════ GODLIKE ═════════════════

    "Cửu Vĩ Hoa Linh": {
    "name": "Hoa Linh Giáng Thế",
    "cooldown": 6,
    "tags": ["Mage", "AoE", "Control"],
    "description": "Gây sát thương diện rộng và stun toàn bộ.",
    },

    "Ác Quỷ Void": {
        "name": "Bản Năng Sát Thủ",
        "cooldown": 4,
        "tags": ["ADC", "Burst"],
        "description": "Lao tới gây sát thương cực lớn.",
    },

    "Thiên Thần Sa Ngã": {
        "name": "Xiềng Xích Bóng Tối",
        "cooldown": 4,
        "tags": ["Mage", "Control"],
        "description": "Trói chân và gây sát thương phép.",
    },

    "Thiên Sứ Phán Xét": {
        "name": "Phán Quyết",
        "cooldown": 5,
        "tags": ["Warrior", "Buff"],
        "description": "Tăng ATK và miễn tử ngắn hạn.",
    },

    "Cục Đá Biết Bay": {
        "name": "Không Thể Cản Phá",
        "cooldown": 5,
        "tags": ["Tank", "AoE"],
        "description": "Lao xuống gây stun diện rộng.",
    },

}



def get_skill(character_name: str) -> Skill | None:
    return SKILLS.get(character_name)


MANA_COST_BY_CLASS = {
    "Assassin": 10,
    "ADC": 10,
    "Warrior": 15,
    "Mage": 15,
    "Tank": 20,
}

MANA_COST_BY_RARITY = {
    "Common": 0,
    "Uncommon": 0,
    "Rare": 0,
    "Epic": 0,
    "Mythic": 5,
    "Legendary": 5,
    "Godlike": 10,
}


def get_skill_mana_cost(character_name: str) -> int:
    character = next((c for c in CHARACTERS if c["name"] == character_name), None)
    if not character:
        return 15

    base_cost = MANA_COST_BY_CLASS.get(character["class"], 15)
    rarity_bonus = MANA_COST_BY_RARITY.get(character["rarity"], 0)
    return max(10, base_cost + rarity_bonus)


def ensure_all_characters_have_skills() -> None:
    names = {c["name"] for c in CHARACTERS}
    missing = sorted(names - set(SKILLS))
    extra = sorted(set(SKILLS) - names)
    if missing or extra:
        msg = "Skill data mismatch."
        if missing:
            msg += f" Missing: {missing}."
        if extra:
            msg += f" Extra: {extra}."
        raise ValueError(msg)


ensure_all_characters_have_skills()
