import random

from core.database import get_team, get_character_by_id, get_weapons_of_char
from core.skill_engine import alive_units, prepare_combatant, take_turn
from core.ui import get_character_icon, get_character_avatar, get_weapon_icon
from core.game_data import CHARACTERS  
from core.weapon_data import WEAPONS, generate_weapon_instance

# Bảng hệ số sức mạnh dựa trên Độ hiếm (Giống hệ thống Gacha của bạn)
MULTIPLIER = {
    "Common": 1.0,
    "Uncommon": 1.1,
    "Rare": 1.25,
    "Epic": 1.5,
    "Mythic": 2.0,
    "Legendary": 2.5,
    "Godlike": 3.0
}

# Tỉ lệ xuất hiện của quái vật (Bạn có thể tinh chỉnh sau này nếu muốn quái dễ/khó hơn)
MONSTER_RARITY_RATES = {
    "Common": 0.45,
    "Uncommon": 0.25,
    "Rare": 0.15,
    "Epic": 0.08,
    "Mythic": 0.015,
    "Legendary": 0.001,
    "Godlike": 0.0001
}

def character_to_dict(c):
    if not c: return None
    return {
        "id": c[0], "name": c[2], "class": c[3], "rarity": c[4],
        "hp": c[5], "atk_phys": c[6], "atk_magic": c[7],
        "def_phys": c[8], "def_magic": c[9], "spd": c[10], "crit": c[11],
    }

def generate_monsters(bot):
    """Tạo đội hình địch có Độ hiếm và Sức mạnh y hệt cơ chế roll tướng."""
    monster_team = []
    num_monsters = random.randint(1, 3) 

    rarities = list(MONSTER_RARITY_RATES.keys())
    weights = list(MONSTER_RARITY_RATES.values())

    for i in range(num_monsters):
        # 1. Bốc 1 khuôn mẫu tướng gốc
        base_char = random.choice(CHARACTERS)
        
        # 2. Quay "nhân phẩm" cho quái vật
        rolled_rarity = random.choices(rarities, weights=weights, k=1)[0]
        
        # 3. Lấy hệ số sức mạnh tương ứng với độ hiếm vừa quay được
        power_mult = MULTIPLIER[rolled_rarity]
        
        # 4. Nhân hệ số vào chỉ số gốc (Thêm +-10% ngẫu nhiên cho kịch tính)
        monster = {
            "name": f"{base_char.get('name', 'Monster')} (Quái)",
            "hp": int(base_char.get("hp", 100) * power_mult * random.uniform(0.9, 1.1)),
            "atk_phys": int(base_char.get("atk_phys", 0) * power_mult * random.uniform(0.9, 1.1)),
            "atk_magic": int(base_char.get("atk_magic", 0) * power_mult * random.uniform(0.9, 1.1)),
            "def_phys": int(base_char.get("def_phys", 0) * power_mult * random.uniform(0.9, 1.1)),
            "def_magic": int(base_char.get("def_magic", 0) * power_mult * random.uniform(0.9, 1.1)),
            "spd": int(base_char.get("spd", 10) * power_mult * random.uniform(0.9, 1.1)),
            "crit": base_char.get("crit", 0), 
            "rarity": rolled_rarity,  # Gán nhãn độ hiếm cho quái để hiện lên Thẻ
            "class": base_char.get("class", "Warrior"),
            "mana": 0, 
            "mana_max": 100 
        }

        # 30% có vũ khí
        monster["equipped_weapon_emojis"] = []
        monster["equipped_weapons"] = []
        monster["weapon_passives"] = []
        if random.random() < 0.3:
            w_inst = generate_weapon_instance()
            w_code = w_inst["code"]
            w_data = WEAPONS.get(w_code) or {}

            for stat, val in w_inst.get("stats", {}).items():
                if stat in monster:
                    monster[stat] += val

            w_emoji_str = get_weapon_icon(w_data.get("emoji", ""), bot=bot)
            monster["equipped_weapon_emojis"].append(w_emoji_str)
            monster["equipped_weapons"].append(w_emoji_str)

            passive = dict(w_data.get("passive") or {})
            if passive:
                passive.update({"source_id": None, "weapon_code": w_code, "rarity": w_inst.get("rarity")})
                monster["weapon_passives"].append(passive)

        m_combatant = prepare_combatant(monster)
        m_combatant["emoji"] = get_character_icon(base_char.get("name", ""), bot=bot)
        m_combatant["avatar"] = get_character_avatar(base_char.get("name", ""), bot=bot)
        m_combatant["max_hp"] = max(1, m_combatant.get("hp", 1))
        monster_team.append(m_combatant)
        
    return monster_team

def snapshot(player, enemy, log, turn):
    return {
        "player": [dict(p) for p in player] if player else [],
        "enemy": [dict(e) for e in enemy] if enemy else [],
        "log": log or "",
        "turn": turn or 0,
    }

def build_team(user_id, bot):
    team_data = get_team(user_id)
    if not team_data: return None
    team = []
    slots = team_data[1:6] 
    for slot in slots:
        if not slot: continue
        char_row = get_character_by_id(slot, user_id)
        if not char_row: continue
        combatant = character_to_dict(char_row)
        
        weapons = get_weapons_of_char(combatant["id"])
        combatant["equipped_weapon_emojis"] = []
        combatant["equipped_weapons"] = []
        combatant["weapon_passives"] = []
        for w in weapons:
            combatant["atk_phys"] += w[2]
            combatant["atk_magic"] += w[3]
            combatant["def_phys"] += w[4]
            combatant["def_magic"] += w[5]
            combatant["crit"] += w[6]
            combatant["spd"] += w[7]
            combatant["hp"] += int(w[8] or 0)

            w_code = w[1]
            w_rarity = (w[9] if len(w) > 9 else None) or (WEAPONS.get(w_code) or {}).get("rarity", "Common")
            w_data = WEAPONS.get(w_code)
            if w_data:
                w_emoji_str = get_weapon_icon(w_data.get("emoji", ""), bot=bot)
                combatant["equipped_weapon_emojis"].append(w_emoji_str)
                combatant["equipped_weapons"].append(w_emoji_str)

                passive = dict(w_data.get("passive") or {})
                if passive:
                    passive.update({"source_id": w[0], "weapon_code": w_code, "rarity": w_rarity})
                    combatant["weapon_passives"].append(passive)
        
        c_ready = prepare_combatant(combatant)
        c_ready["emoji"] = get_character_icon(c_ready["name"], bot=bot)
        c_ready["avatar"] = get_character_avatar(c_ready["name"], bot=bot)
        c_ready["max_hp"] = max(1, c_ready.get("hp", 1)) 
        team.append(c_ready)
    return team

def fight_with_history(user_id, bot):
    team = build_team(user_id, bot)
    if not team: return "no_team"
    
    monsters = generate_monsters(bot)
    
    log, history, turn = [], [], 0
    history.append(snapshot(team, monsters, "Bắt đầu cuộc đi săn", turn))

    while alive_units(team) and alive_units(monsters) and turn < 50:
        all_units = alive_units(team) + alive_units(monsters)
        all_units.sort(key=lambda x: x.get('spd', 0), reverse=True) 

        for unit in all_units:
            if unit.get('hp', 0) <= 0: continue
            
            if unit in team:
                targets = alive_units(monsters)
                friends = team
            else:
                targets = alive_units(team)
                friends = monsters
            
            if not targets: break

            log_text = take_turn(unit, targets, friends, rng=random)
            if log_text:
                log.append(log_text)
                turn += 1
                history.append(snapshot(team, monsters, log_text, turn))
            
            if not alive_units(team) or not alive_units(monsters): break

    outcome = "win" if alive_units(team) else "lose"
    return outcome, log, team, monsters, history

def fight_pvp_with_history(user_id_1, user_id_2, bot):
    team_1 = build_team(user_id_1, bot)
    team_2 = build_team(user_id_2, bot)
    if not team_1 or not team_2:
        return "error", [], [], [], []

    log, history, turn = [], [], 0
    history.append(snapshot(team_1, team_2, "Start PvP", turn))

    while alive_units(team_1) and alive_units(team_2) and turn < 50:
        all_units = alive_units(team_1) + alive_units(team_2)
        all_units.sort(key=lambda x: x.get('spd', 0), reverse=True)

        for unit in all_units:
            if unit.get('hp', 0) <= 0: continue
            
            if unit in team_1:
                targets = alive_units(team_2)
                friends = team_1
            else:
                targets = alive_units(team_1)
                friends = team_2
            
            if not targets: break

            log_text = take_turn(unit, targets, friends, rng=random)
            if log_text:
                log.append(log_text)
                turn += 1
                history.append(snapshot(team_1, team_2, log_text, turn))

            if not alive_units(team_1) or not alive_units(team_2):
                break

    outcome = "p1_win" if alive_units(team_1) else "p2_win"
    return outcome, log, team_1, team_2, history
