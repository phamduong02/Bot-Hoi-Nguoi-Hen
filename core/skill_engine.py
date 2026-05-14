from __future__ import annotations

import random
from typing import Iterable

from core.skill_data import get_skill, get_skill_mana_cost


MANA_PER_BASIC_ATTACK = 5


def _iter_weapon_passives(unit: dict) -> list[dict]:
    passives = unit.get("weapon_passives", ())
    if not passives:
        return []
    return list(passives)


def _weapon_state(unit: dict) -> dict:
    return unit.setdefault("_weapon_state", {})


def _passive_source_key(passive: dict) -> str:
    weapon_code = passive.get("weapon_code") or passive.get("code") or passive.get("weapon") or ""
    source_id = passive.get("source_id")
    if source_id is None:
        return f"{weapon_code}:{passive.get('id')}"
    return f"{weapon_code}:{source_id}"


def _init_weapon_passives(unit: dict) -> None:
    state = _weapon_state(unit)
    if state.get("inited"):
        return

    state["inited"] = True
    passives = _iter_weapon_passives(unit)
    if not passives:
        return

    # Justice: pick 1 mode per weapon for the whole battle
    justice_mode: dict[str, str] = {}
    for passive in passives:
        if passive.get("id") != "justice":
            continue
        source = _passive_source_key(passive)
        justice_mode[source] = random.choice(("damage", "lifesteal"))
    if justice_mode:
        state["justice_mode"] = justice_mode

    # Static buffs applied once at battle start
    amp_magic_rate = sum(
        float(p.get("rate") or 0)
        for p in passives
        if p.get("id") == "amp_magic"
    )
    if amp_magic_rate > 0:
        base = int(unit.get("atk_magic", 0))
        bonus = int(base * amp_magic_rate)
        if bonus:
            unit["atk_magic"] = base + bonus
            state["amp_magic_bonus"] = state.get("amp_magic_bonus", 0) + bonus


def _weapon_crit_bonus_add(attacker: dict) -> float:
    bonus = 0.0
    for passive in _iter_weapon_passives(attacker):
        if passive.get("id") == "crit_damage":
            bonus += float(passive.get("bonus") or 0.0)
    return bonus


def _weapon_damage_multiplier(attacker: dict, defender: dict) -> float:
    passives = _iter_weapon_passives(attacker)
    if not passives:
        return 1.0

    state = _weapon_state(attacker)
    mult = 1.0
    for passive in passives:
        passive_id = passive.get("id")
        source = _passive_source_key(passive)

        if passive_id == "justice":
            mode = (state.get("justice_mode") or {}).get(source, "damage")
            if mode == "damage":
                mult *= 1.0 + float(passive.get("damage_bonus") or 0.0)

        elif passive_id == "damage_bonus":
            mult *= 1.0 + float(passive.get("bonus") or 0.0)

        elif passive_id == "damage_vs_high_hp":
            threshold_hp = int(passive.get("threshold_hp") or 0)
            if threshold_hp > 0:
                target_max_hp = max(1, defender.get("max_hp", defender.get("hp", 1)))
                if target_max_hp >= threshold_hp:
                    mult *= 1.0 + float(passive.get("bonus") or 0.0)

    return mult


def _try_trigger_low_hp_shield(unit: dict) -> None:
    passives = _iter_weapon_passives(unit)
    if not passives:
        return

    state = _weapon_state(unit)
    for passive in passives:
        if passive.get("id") != "shield_low_hp":
            continue

        source = _passive_source_key(passive)
        used_key = f"shield_used:{source}"
        if state.get(used_key):
            continue

        threshold = float(passive.get("threshold") or 0.4)
        shield_ratio = float(passive.get("shield_ratio") or 0.0)
        if shield_ratio <= 0:
            continue

        if hp_ratio(unit) <= threshold:
            shield_amount = int(max(1, unit.get("max_hp", unit.get("hp", 1))) * shield_ratio)
            grant_shield(unit, shield_amount)
            state[used_key] = True


def _apply_turn_start_weapon_passives(unit: dict) -> None:
    passives = _iter_weapon_passives(unit)
    if not passives:
        return

    _try_trigger_low_hp_shield(unit)

    state = _weapon_state(unit)
    for passive in passives:
        passive_id = passive.get("id")
        source = _passive_source_key(passive)

        if passive_id == "regen":
            rate = float(passive.get("rate") or 0.0)
            if rate > 0:
                heal_amount = int(max(1, unit.get("max_hp", unit.get("hp", 1))) * rate)
                heal_target(unit, max(1, heal_amount))

        elif passive_id == "ramp_magic":
            amount = int(passive.get("amount") or 0)
            if amount:
                unit["atk_magic"] = unit.get("atk_magic", 0) + amount

        elif passive_id == "giant_growth":
            max_stacks = int(passive.get("max_stacks") or 0)
            if max_stacks <= 0:
                continue

            stacks_key = f"giant_stacks:{source}"
            stacks = int(state.get(stacks_key, 0))
            if stacks >= max_stacks:
                continue

            stacks += 1
            state[stacks_key] = stacks

            atk = int(passive.get("atk") or 0)
            defense = int(passive.get("def") or 0)
            if atk:
                unit["atk_phys"] = unit.get("atk_phys", 0) + atk
                unit["atk_magic"] = unit.get("atk_magic", 0) + atk
            if defense:
                unit["def_phys"] = unit.get("def_phys", 0) + defense
                unit["def_magic"] = unit.get("def_magic", 0) + defense

            if stacks >= max_stacks and not state.get(f"giant_hp:{source}"):
                bonus_hp = int(passive.get("bonus_hp") or 0)
                if bonus_hp > 0:
                    unit["max_hp"] = max(1, unit.get("max_hp", unit.get("hp", 1))) + bonus_hp
                    unit["hp"] = unit.get("hp", 0) + bonus_hp
                state[f"giant_hp:{source}"] = True


def _apply_weapon_on_hit(attacker: dict, defender: dict, dealt: int, is_skill: bool) -> None:
    if dealt <= 0:
        return

    passives = _iter_weapon_passives(attacker)
    if not passives:
        return

    state = _weapon_state(attacker)
    for passive in passives:
        passive_id = passive.get("id")
        source = _passive_source_key(passive)

        if passive_id == "lifesteal":
            rate = float(passive.get("rate") or 0.0)
            if rate > 0:
                heal_target(attacker, max(1, int(dealt * rate)))

        elif passive_id == "justice":
            mode = (state.get("justice_mode") or {}).get(source, "damage")
            if mode == "lifesteal":
                rate = float(passive.get("lifesteal_bonus") or 0.0)
                if rate > 0:
                    heal_target(attacker, max(1, int(dealt * rate)))

        elif passive_id == "mana_on_hit" and not is_skill:
            amount = int(passive.get("amount") or 0)
            if amount > 0:
                add_mana(attacker, amount)

        elif passive_id == "stack_spd_on_hit":
            amount = int(passive.get("amount") or 0)
            if amount:
                attacker["spd"] = attacker.get("spd", 0) + amount


def _apply_weapon_on_damage_taken(defender: dict, attacker: dict, dealt: int) -> None:
    if dealt <= 0:
        return

    passives = _iter_weapon_passives(defender)
    if not passives:
        return

    _try_trigger_low_hp_shield(defender)

    for passive in passives:
        if passive.get("id") != "reflect":
            continue

        rate = float(passive.get("rate") or 0.0)
        if rate <= 0:
            continue

        reflect_dmg = int(dealt * rate)
        if reflect_dmg > 0:
            apply_damage(attacker, reflect_dmg)


def prepare_combatant(combatant: dict) -> dict:
    prepared = dict(combatant)
    prepared["max_hp"] = prepared.get("max_hp", prepared.get("hp", 0))
    prepared["mana"] = prepared.get("mana", 0)
    if get_skill(prepared.get("name", "")):
        prepared["mana_max"] = prepared.get(
            "mana_max",
            get_skill_mana_cost(prepared.get("name", "")),
        )
    else:
        prepared["mana_max"] = 0
    prepared["shield"] = prepared.get("shield", 0)
    prepared["stun"] = prepared.get("stun", 0)
    _init_weapon_passives(prepared)
    return prepared


def alive_units(units: Iterable[dict]) -> list[dict]:
    return [unit for unit in units if unit.get("hp", 0) > 0]


def hp_ratio(unit: dict) -> float:
    max_hp = max(1, unit.get("max_hp", unit.get("hp", 1)))
    return unit.get("hp", 0) / max_hp


def choose_target(units: Iterable[dict], prefer_low_hp: bool = False, rng=None) -> dict | None:
    alive = alive_units(units)
    if not alive:
        return None

    if prefer_low_hp:
        return min(
            alive,
            key=lambda unit: (
                hp_ratio(unit),
                unit.get("hp", 0),
                unit.get("name", ""),
            ),
        )

    random_source = rng or random
    return random_source.choice(alive)


def grant_shield(target: dict, amount: int) -> int:
    if amount <= 0:
        return 0

    target["shield"] = target.get("shield", 0) + amount
    return amount


def heal_target(target: dict, amount: int) -> int:
    if amount <= 0:
        return 0

    max_hp = max(1, target.get("max_hp", target.get("hp", 1)))
    before = target.get("hp", 0)
    target["hp"] = min(max_hp, before + amount)
    return target["hp"] - before


def apply_damage(target: dict, damage: int) -> tuple[int, int]:
    if damage <= 0:
        return 0, 0

    shield = max(0, target.get("shield", 0))
    absorbed = min(shield, damage)
    if absorbed:
        target["shield"] = shield - absorbed

    hp_damage = damage - absorbed
    if hp_damage:
        target["hp"] = max(0, target.get("hp", 0) - hp_damage)

    return hp_damage, absorbed


def add_mana(attacker: dict, amount: int = MANA_PER_BASIC_ATTACK) -> int:
    if amount <= 0:
        return attacker.get("mana", 0)

    mana_max = max(0, attacker.get("mana_max", 0))
    current = attacker.get("mana", 0)
    if mana_max > 0:
        current = min(mana_max, current + amount)
    else:
        current += amount

    attacker["mana"] = current
    return current


def _uses_magic(attacker: dict, skill_tags: set[str] | None = None) -> bool:
    if skill_tags:
        if {"mage", "healer", "support", "magic"} & skill_tags:
            return True

    return attacker.get("atk_magic", 0) > attacker.get("atk_phys", 0)


def calculate_damage(
    attacker: dict,
    defender: dict,
    scale: float = 1.0,
    magic_attack: bool | None = None,
    crit_bonus: float = 1.5,
    rng=None,
) -> tuple[int, bool]:
    attack_is_magic = _uses_magic(attacker) if magic_attack is None else magic_attack

    attack_key = "atk_magic" if attack_is_magic else "atk_phys"
    defense_key = "def_magic" if attack_is_magic else "def_phys"
    secondary_key = "atk_phys" if attack_is_magic else "atk_magic"

    primary_attack = attacker.get(attack_key, 0)
    secondary_attack = attacker.get(secondary_key, 0)
    defense = defender.get(defense_key, 0)

    damage = int(primary_attack * scale + secondary_attack * 0.25)
    damage -= defense // 2
    if damage < 1:
        damage = 1

    crit_chance = max(0, int(attacker.get("crit", 0)))
    is_crit = False
    random_source = rng or random
    if crit_chance and random_source.randrange(100) < crit_chance:
        damage = int(damage * crit_bonus)
        is_crit = True

    return max(1, damage), is_crit


def basic_attack_turn(attacker: dict, defenders: list[dict], rng=None) -> str | None:
    target = choose_target(defenders, rng=rng)
    if not target:
        return None

    attack_is_magic = _uses_magic(attacker)
    crit_bonus = 1.5 + _weapon_crit_bonus_add(attacker)
    damage, is_crit = calculate_damage(
        attacker,
        target,
        scale=1.0,
        magic_attack=attack_is_magic,
        crit_bonus=crit_bonus,
        rng=rng,
    )
    damage = int(max(1, damage * _weapon_damage_multiplier(attacker, target)))
    dealt, absorbed = apply_damage(target, damage)
    add_mana(attacker, MANA_PER_BASIC_ATTACK)
    _apply_weapon_on_hit(attacker, target, dealt, is_skill=False)
    _apply_weapon_on_damage_taken(target, attacker, dealt)

    if absorbed and dealt:
        return (
            f"{attacker['name']} hits {target['name']} for {dealt} damage "
            f"({absorbed} shield) (+5 mana)"
        )
    if absorbed and not dealt:
        return (
            f"{attacker['name']} hits {target['name']} but the shield blocks it "
            f"({absorbed} shield) (+5 mana)"
        )
    if is_crit:
        return f"{attacker['name']} crits {target['name']} for {dealt} damage (+5 mana)"
    return f"{attacker['name']} hits {target['name']} for {dealt} damage (+5 mana)"


def _grant_defense_shred(target: dict, attacker: dict) -> int:
    shred_amount = max(1, int((attacker.get("atk_phys", 0) + attacker.get("atk_magic", 0)) * 0.08))
    target["def_phys"] = max(0, target.get("def_phys", 0) - shred_amount)
    target["def_magic"] = max(0, target.get("def_magic", 0) - shred_amount)
    return shred_amount


def _skill_scale(tags: set[str]) -> float:
    scale = 1.1

    if "burst" in tags:
        scale += 0.65
    elif "execute" in tags:
        scale += 0.55
    elif "damage" in tags:
        scale += 0.40
    elif "control" in tags:
        scale += 0.25
    elif "drain" in tags:
        scale += 0.30
    elif "tank" in tags:
        scale += 0.15

    return scale


def cast_skill_turn(attacker: dict, defenders: list[dict], allies: list[dict], rng=None) -> str | None:
    skill = get_skill(attacker.get("name", "")) or {}
    skill_name = skill.get("name", "Skill")
    tags = {str(tag).lower() for tag in skill.get("tags", ())}
    attacker["mana"] = 0

    alive_defenders = alive_units(defenders)
    alive_allies = alive_units(allies)

    if "healer" in tags:
        if not alive_allies:
            return f"{attacker['name']} casts {skill_name}, but no allies remain."

        heal_amount = max(1, int(attacker.get("atk_magic", 0) * 0.65 + attacker.get("max_hp", 0) * 0.08))
        total_healed = 0
        for ally in alive_allies:
            total_healed += heal_target(ally, heal_amount)

        if "support" in tags:
            shield_target = choose_target(alive_allies, prefer_low_hp=True, rng=rng)
            if shield_target:
                shield_amount = max(1, heal_amount // 2)
                grant_shield(shield_target, shield_amount)
                return (
                    f"{attacker['name']} casts {skill_name}, healing the team for {total_healed} "
                    f"and shielding {shield_target['name']} for {shield_amount}"
                )

        return f"{attacker['name']} casts {skill_name}, restoring {total_healed} HP to the team"

    if "support" in tags:
        if not alive_allies:
            return f"{attacker['name']} casts {skill_name}, but no allies remain."

        heal_target_unit = choose_target(alive_allies, prefer_low_hp=True, rng=rng)
        if not heal_target_unit:
            return f"{attacker['name']} casts {skill_name}, but no ally can be helped."

        heal_amount = max(1, int(attacker.get("atk_magic", 0) * 0.55 + attacker.get("max_hp", 0) * 0.06))
        healed = heal_target(heal_target_unit, heal_amount)
        shield_amount = max(1, heal_amount // 2)
        grant_shield(heal_target_unit, shield_amount)
        return (
            f"{attacker['name']} casts {skill_name}, healing {heal_target_unit['name']} for {healed} "
            f"and granting {shield_amount} shield"
        )

    if not alive_defenders:
        return None

    prefer_low_hp = "execute" in tags
    attack_is_magic = _uses_magic(attacker, tags)
    scale = _skill_scale(tags)
    crit_bonus = 1.8 if "crit" in tags else 1.5
    aoe = "aoe" in tags or "boss" in tags
    target = choose_target(alive_defenders, prefer_low_hp=prefer_low_hp, rng=rng)

    if aoe:
        total_damage = 0
        target_names: list[str] = []
        for defender in alive_defenders:
            damage, _ = calculate_damage(
                attacker,
                defender,
                scale=scale * 0.85,
                magic_attack=attack_is_magic,
                crit_bonus=crit_bonus + _weapon_crit_bonus_add(attacker),
                rng=rng,
            )

            if "execute" in tags and hp_ratio(defender) <= 0.35:
                damage = int(damage * 1.35)

            damage = int(max(1, damage * _weapon_damage_multiplier(attacker, defender)))
            dealt, absorbed = apply_damage(defender, damage)
            total_damage += dealt
            target_names.append(defender["name"])

            _apply_weapon_on_hit(attacker, defender, dealt, is_skill=True)
            _apply_weapon_on_damage_taken(defender, attacker, dealt)

            if "control" in tags and defender.get("hp", 0) > 0:
                defender["stun"] = max(defender.get("stun", 0), 1)

            if "shred" in tags and defender.get("hp", 0) > 0:
                _grant_defense_shred(defender, attacker)

        if "tank" in tags or "reflect" in tags:
            shield_amount = max(1, int(attacker.get("def_phys", 0) * 0.45 + attacker.get("max_hp", 0) * 0.06))
            grant_shield(attacker, shield_amount)

        if "drain" in tags:
            heal_target(attacker, max(1, total_damage // 2))

        if "reset" in tags:
            heal_target(attacker, max(1, int(attacker.get("max_hp", 0) * 0.25)))

        if "mobility" in tags:
            heal_target(attacker, max(1, int(attacker.get("max_hp", 0) * 0.08)))

        return (
            f"{attacker['name']} casts {skill_name}, hitting {', '.join(target_names)} "
            f"for {total_damage} total damage"
        )

    if not target:
        return None

    damage, is_crit = calculate_damage(
        attacker,
        target,
        scale=scale,
        magic_attack=attack_is_magic,
        crit_bonus=crit_bonus + _weapon_crit_bonus_add(attacker),
        rng=rng,
    )

    if "execute" in tags and hp_ratio(target) <= 0.35:
        damage = int(damage * 1.45)

    damage = int(max(1, damage * _weapon_damage_multiplier(attacker, target)))
    dealt, absorbed = apply_damage(target, damage)

    _apply_weapon_on_hit(attacker, target, dealt, is_skill=True)
    _apply_weapon_on_damage_taken(target, attacker, dealt)

    if "control" in tags and target.get("hp", 0) > 0:
        target["stun"] = max(target.get("stun", 0), 1)

    if "shred" in tags and target.get("hp", 0) > 0:
        _grant_defense_shred(target, attacker)

    if "tank" in tags or "reflect" in tags:
        shield_amount = max(1, int(attacker.get("def_phys", 0) * 0.45 + attacker.get("max_hp", 0) * 0.06))
        grant_shield(attacker, shield_amount)

    if "drain" in tags:
        heal_target(attacker, max(1, dealt // 2))

    if "reset" in tags:
        heal_target(attacker, max(1, int(attacker.get("max_hp", 0) * 0.25)))

    if "mobility" in tags:
        heal_target(attacker, max(1, int(attacker.get("max_hp", 0) * 0.08)))

    if absorbed and dealt:
        return (
            f"{attacker['name']} casts {skill_name} on {target['name']} for {dealt} damage "
            f"({absorbed} shield)"
        )
    if absorbed and not dealt:
        return (
            f"{attacker['name']} casts {skill_name} on {target['name']}, but the shield blocks it "
            f"({absorbed} shield)"
        )
    if is_crit:
        return f"{attacker['name']} casts {skill_name} on {target['name']} for {dealt} damage (crit)"
    return f"{attacker['name']} casts {skill_name} on {target['name']} for {dealt} damage"


def take_turn(attacker: dict, defenders: list[dict], allies: list[dict], rng=None) -> str | None:
    if attacker.get("hp", 0) <= 0:
        return None

    _apply_turn_start_weapon_passives(attacker)

    if attacker.get("stun", 0) > 0:
        attacker["stun"] = attacker.get("stun", 0) - 1
        return f"{attacker['name']} is stunned and skips the turn"

    mana_max = max(0, attacker.get("mana_max", 0))
    if mana_max > 0 and attacker.get("mana", 0) >= mana_max:
        return cast_skill_turn(attacker, defenders, allies, rng=rng)

    return basic_attack_turn(attacker, defenders, rng=rng)
