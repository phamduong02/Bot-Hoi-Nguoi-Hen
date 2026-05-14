import random

from core.weapon_data import generate_weapon_instance


def drop_weapon():
    """Optional drop helper (legacy). Returns weapon instance dict or None."""
    if random.random() < 0.5:
        return generate_weapon_instance()
    return None

