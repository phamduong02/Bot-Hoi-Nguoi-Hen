import time

cooldowns = {}

def check_cooldown(user_id, command, seconds):
    now = time.time()

    if user_id not in cooldowns:
        cooldowns[user_id] = {}

    last = cooldowns[user_id].get(command, 0)

    if now - last < seconds:
        return False, int(seconds - (now - last))

    cooldowns[user_id][command] = now
    return True, 0