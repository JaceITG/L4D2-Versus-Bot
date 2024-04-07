

# TODO: generate a unique incremental q_id respecting existing database entities
next_available_id = 0
async def gen_q_id():
    global next_available_id

    next_available_id += 1
    return next_available_id-1

gamemode_strs = {
        "standard": {"title": "Standard Vanilla+", "desc": "Minor QoL and balance plugins; see ⁠dedicated-server-info for more information!"},
        "realism" : {"title": "Realism", "desc": "Survivors can't see player or item outlines; common infected are more resilient; Witches kill instantly!"},
        "survival": {"title": "Survival", "desc": "Survivors hold out in a small arena; teams swap; the Survivor team with the longest time alive wins!"},
        "jockey"  : {"title": "Riding My Survivor", "desc": "Jockeys are the only Special Infected; Jockey HP, DMG, and speed are significantly increased!"},
        "scavenge": {"title": "Scavenge", "desc": "Survivors collect gas cans in a small arena; teams swap; the Survivor team with the most gas cans wins!"},
        "bleed"   : {"title": "Bleed Out", "desc": "Survivors only have temporary HP; First Aid Kits are replaced with Adrenaline and Pain Pills!"},
        "tank"    : {"title": "Taaannnkk!", "desc": "Only Tanks spawn; First Aid Kits are replaced with Adrenaline and Pain Pills!"},
        "hpack"   : {"title": "Healthpackalypse!", "desc": "All health items are removed from spawn pools!"},
        "confogl" : {"title": "Confogl", "desc": "First Aid Kits are removed; more Adrenaline and Pain Pills spawn; only Tier-1 weapons!"},
        "l4d1"    : {"title": "Left 4 Dead 1", "desc": "This queue is for Left 4 Dead 1, NOT L4D2!"},
        "l4d2"    : {"title": "unmodded L4D2", "desc": "No plugins or alterations of any kind; this is pure vanilla Left 4 Dead 2!"},
    }
def queue_message(gamemode):

    if gamemode not in gamemode_strs.keys():
        raise ValueError

    # Fill in template with attributes for selected game type
    return (
        f"{carriers_role.mention} {ksobs_role.mention}\n" 
        f"A **__{gamemode_strs[gamemode]['title']}__** versus game is being set up for 8 players!\n"
        
        f"{("No Charger, Jockey, or Spitter, but Boomers can vomit instantly after spawning/while being shoved, Hunters deal damage faster, and Smokers are\n"
            "hitscan.  Tanks throw rocks quicker and move faster when on fire.  Witches kill downed Survivors faster.\n\n"
            "Small firearm arsenal, superior pistols, no melee weapons, generally faster-paced than L4D2 Versus with less camping/baiting. The score is\n" 
            "determined by Survivor HP at the end of a level and a per-map difficulty modifier.\n\n") if gamemode == "l4d1" else ""}"

        f"({gamemode_strs[gamemode]['desc']})\n\n"
        "To join the queue, react to this message with ✅\n"
        "To join as a sub, react to this message with <:Substitute:984524545866219631>\n\n"
        "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
        f"Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you {"own Left 4 Dead 1 and" if gamemode=="l4d1" else ""} have at least two hours available.**\n\n" 
        f"Please report any issues to {zeusMention}"
    )
