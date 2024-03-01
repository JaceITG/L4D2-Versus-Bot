import discord
from discord.ext import commands
import random
import asyncio
import os
import datetime
import json

BOT_TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.all()
intents.members = True
intents.reactions = True

zeuskriegID = "1148387726719189103"

queue_in_progress = False

emoji_ids = {
    '1_Vanilla': 1211013206915416146,
    '2_Vanilla': 1211013201081405490,
    '3_Vanilla': 1211013205862916216,
    '1_Custom': 1211013208022978591,
    '2_Custom': 1211013204382195753,
    '3_Custom': 1211013202637365308,
    'Left_4_Dead': 1211015141840130068,
}


bot = commands.Bot(command_prefix='!', intents=intents)

reacted_users = {
    'queue': set(),
    'sub': set()
}

participants_names = []

with open('maps/campaign_maps.json', 'r') as file:
    vanilla_maps_data = json.load(file)

with open('maps/custom_maps.json', 'r') as file:
    custom_maps_data = json.load(file)

async def decrement_timeout():
    # Load and update vanilla maps
    with open('maps/campaign_maps.json', 'r') as file:
        vanilla_maps_data = json.load(file)
        for map_info in vanilla_maps_data['maps']:
            if map_info['timeout'] > 0:
                map_info['timeout'] -= 1
                if map_info['timeout'] < 0:
                    map_info['timeout'] = 0

    # Write updated vanilla maps data back to JSON file
    with open('maps/campaign_maps.json', 'w') as file:
        json.dump(vanilla_maps_data, file, indent=4)

    # Load and update custom maps
    with open('maps/custom_maps.json', 'r') as file:
        custom_maps_data = json.load(file)
        for map_info in custom_maps_data['maps']:
            if map_info['timeout'] > 0:
                map_info['timeout'] -= 1
                if map_info['timeout'] < 0:
                    map_info['timeout'] = 0

    # Write updated custom maps data back to JSON file
    with open('maps/custom_maps.json', 'w') as file:
        json.dump(custom_maps_data, file, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Try !queue standard"))

@bot.command()
async def queue(ctx, queue_type):
    global queue_in_progress
    allowed_role = discord.utils.get(ctx.guild.roles, name='Matchmaker')
    if allowed_role in ctx.author.roles:
        # Proceed with the queue process if the user has the allowed role
        if queue_in_progress:
            await ctx.send("A queue is already in progress. Please wait for the current one to finish.")
            return
        else:
            queue_in_progress = True
            await queue_process(ctx, queue_type)
    else:
        with open('img/coach.jpg', 'rb') as file:
            image = discord.File(file)
        await ctx.send(file=image)
        await ctx.send("Shut the fuck up.")

@bot.command()
async def voting(ctx, queue_type):
    global participants_names, reacted_users
    global queue_in_progress

    with open('maps/campaign_maps.json', 'r') as file:
        available_vanilla_maps = json.load(file)
        available_vanilla_maps_filtered = [map_info for map_info in available_vanilla_maps['maps'] if map_info['timeout'] == 0]
        selected_vanilla_maps = random.sample(available_vanilla_maps_filtered, min(3, len(available_vanilla_maps_filtered)))

    with open('maps/custom_maps.json', 'r') as file:
        available_custom_maps = json.load(file)
        available_custom_maps_filtered = [map_info for map_info in available_custom_maps['maps'] if map_info['timeout'] == 0]
        selected_customs = random.sample(available_custom_maps_filtered, min(3, len(available_custom_maps_filtered)))

    vote_message = (
        f"Vote for the campaign you'd like to play! The campaign with the most votes wins. Tied campaigns will be chosen at random.\n\n"
        f"`=== Vanilla Campaigns ===`\n"
    )

    for i, map_name in enumerate(selected_vanilla_maps, start=1):
        vote_message += f"<:{i}_Vanilla:{emoji_ids[str(i)+'_Vanilla']}> {map_name['name']}\n"

    vote_message += "`=== Custom Campaigns ===`\n"
    for i, map_name in enumerate(selected_customs, start=1):
        vote_message += f"<:{i}_Custom:{emoji_ids[str(i)+'_Custom']}> {map_name['name']}\n"

    vote_message += (
        f"\n<:Left_4_Dead:{emoji_ids['Left_4_Dead']}> Reroll the maps\n"
        f"Missing our custom campaigns? Download them here: <https://steamcommunity.com/sharedfiles/filedetails/?id=3023799326>"
    )

    # Send the voting message
    vote_msg = await ctx.send(vote_message)

    # Add reactions to the voting message
    reactions = [f'<:{emoji_name}:{emoji_id}>' for emoji_name, emoji_id in emoji_ids.items()]

    def check_reaction(reaction, user):
        return user == ctx.author and str(reaction.emoji) in reactions and user != ctx.bot.user

    for reaction in reactions:
        await vote_msg.add_reaction(reaction)

    # Wait for reactions for 60 seconds
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check_reaction)
        except asyncio.TimeoutError:
            break  # Timeout, end the voting

    # Determine the most voted map
    index = reactions.index(str(reaction.emoji))
    if index == 6:
        await ctx.send("Rerolling maps...")
        await voting(ctx, queue_type)  # Restart the voting process
        return
    if index < 3:
        most_voted_map = selected_vanilla_maps[index]
        most_voted_map_type = "vanilla"
    elif 3 <= index < 6:
        most_voted_map = selected_customs[index - 3]
        most_voted_map_type = "custom"
    else:
        await ctx.send("Invalid vote index.")
        return
    
    most_voted_map['timeout'] = 3
    most_voted_map['amountPlayed'] += 1

    if most_voted_map_type == "vanilla":
        with open('maps/campaign_maps.json', 'w') as file:
            json.dump(available_vanilla_maps, file, indent=4)
    elif most_voted_map_type == "custom":
        with open('maps/custom_maps.json', 'w') as file:
            json.dump(available_custom_maps, file, indent=4)


    balanced_teams = False
    while not balanced_teams:
        random.shuffle(participants_names)
        team_size = len(participants_names) // 2
        team1_names = participants_names[:team_size]
        team2_names = participants_names[team_size:]

        if abs(len(team1_names) - len(team2_names)) <= 1:
            balanced_teams = True

    # Construct team mentions
    team1_mentions = '\n'.join([f'<@{ctx.guild.get_member_named(name).id}>' for name in team1_names])
    team2_mentions = '\n'.join([f'<@{ctx.guild.get_member_named(name).id}>' for name in team2_names])

    # Send the message with the most voted map and assigned teams
    await ctx.send(
        f"**{most_voted_map['name']}** has won and teams have been assigned! "
        f"Please join Pre-Game VC within 10 minutes or you may be subbed out.\n\n"
        f"`Survivors`\n{team1_mentions}\n\n"
        f"`Infected`\n{team2_mentions}\n\n"
    )



    # Notify specific users about the queue information
    specific_user_ids = ["1148387726719189103", "318486548394016789", "317412117240348675"]
    for user_id in specific_user_ids:
        user = await bot.fetch_user(user_id)
        if user:
            try:
                await user.send(
                f"**__Queue Information__**\n\n"
                f"**Date Popped**: {datetime.datetime.utcnow()}\n"
                f"**Queue Type**: {queue_type.capitalize()}\n"
                f"**Campaign**: {most_voted_map}\n"
                f"**Survivors**: {', '.join(team1_names)}\n"
                f"**Infected**: {', '.join(team2_names)}\n"
            )
            except Exception as e:
                print(f"Failed to send queue info to user with ID {user_id}: {e}")

    # Clear the reacted_users and participants_names variables
    queue_in_progress = False
    reacted_users = {'queue': set(), 'sub': set()}
    participants_names = []

# Function to handle the queue process
async def queue_process(ctx, queue_type):
    global reacted_users, participants_names

    participants_names = []

    # Clear all relevant variables and data structures
    reacted_users = {'queue': set(), 'sub': set()}

    # Mention '@Carriers' and '@KSOBS' roles in the queue information message
    carriers_role = discord.utils.get(ctx.guild.roles, name='Carriers')
    ksobs_role = discord.utils.get(ctx.guild.roles, name='Kill All SOBs!')

    zeusMention = f'<@{zeuskriegID}>'
    # Check if roles are found
    if carriers_role is None or ksobs_role is None:
        await ctx.send("Roles not found. Please make sure roles '@Carriers' and '@KSOBS' exist.")
        return

    # Send the queue information message
    queue_messages = {
        'standard': (
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__standard Vanilla+__** versus game is being set up for 8 players!\n"
            "(Minor QoL and balance plugins; see ⁠dedicated-server-info for more information!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"

        ),
        'realism': (
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Realism__** is being set up for 8 players!\n"
            "(Survivors can't see player or item outlines; common infected are more resilient; Witches kill instantly!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'survival':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Survival__** versus game is being set up for 8 players!\n"
            "(Survivors hold out in a small arena; teams swap; the Survivor team with the longest time alive wins!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'jockey':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Riding My Survivor__** versus game is being set up for 8 players!\n"
            "(Jockeys are the only Special Infected; Jockey HP, DMG, and speed are significantly increased!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'scavenge':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Scavenge__** versus game is being set up for 8 players!\n"
            "(Survivors collect gas cans in a small arena; teams swap; the Survivor team with the most gas cans wins!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'bleed':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Bleed Out__** versus game is being set up for 8 players!\n"
            "(Survivors only have temporary HP; First Aid Kits are replaced with Adrenaline and Pain Pills!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'tank':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Taaannnkk!__** versus game is being set up for 8 players!\n"
            "(Only Tanks spawn; First Aid Kits are replaced with Adrenaline and Pain Pills!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'hpack':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Healthpackalypse!__** versus game is being set up for 8 players!\n"
            "(All health items are removed from spawn pools!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'confogl':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Confogl__** versus game is being set up for 8 players!\n"
            "(First Aid Kits are removed; more Adrenaline and Pain Pills spawn; only Tier-1 weapons!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'l4d1':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **Left 4 Dead 1** versus game is being set up for 8 players!\n"
            "**__This queue is for Left 4 Dead 1, NOT L4D2!__**"
            "No Charger, Jockey, or Spitter, but Boomers can vomit instantly after spawning/while being shoved, Hunters deal damage faster, and Smokers are\n"
            "hitscan.  Tanks throw rocks quicker and move faster when on fire.  Witches kill downed Survivors faster.\n\n"

            "Small firearm arsenal, superior pistols, no melee weapons, generally faster-paced than L4D2 Versus with less camping/baiting. The score is\n" 
            "determined by Survivor HP at the end of a level and a per-map difficulty modifier.\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you own Left 4 Dead 1 and have at least two hours\n" 
            "available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'l4d2':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "An **unmodded L4D2** versus game is being set up for 8 players!\n"
            "(No plugins or alterations of any kind; this is pure vanilla Left 4 Dead 2!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with <:Substitute:1211015106029293612>\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        )
    }

    if queue_type not in queue_messages:
        await ctx.send("Invalid queue type. Available types: standard, custom")
        return

    # Send the appropriate queue information message
    queue_msg = await ctx.send(queue_messages[queue_type], delete_after=None)

    await queue_msg.add_reaction("✅")
    await queue_msg.add_reaction("<:Substitute:1211015106029293612>")

    def check(reaction, user):
        return (str(reaction.emoji) == "✅" or str(reaction.emoji) == "<:Substitute:1211015106029293612>") and user != bot.user

    try:
        while len(reacted_users['queue']) < 8:
            reaction, user = await bot.wait_for('reaction_add', timeout=None, check=check)

            if str(reaction.emoji) == "✅":
                reacted_users['queue'].add(user.id)
                participants_names.append(user.name)
            elif str(reaction.emoji) == "<:Substitute:1211015106029293612>":
                reacted_users['sub'].add(user.id)

        for participant_id in reacted_users['queue']:
            participant = await ctx.guild.fetch_member(participant_id)

            try:
                channel_id = "1207495463297875978"
                channel_mention = f"<#{channel_id}>"
                await participant.send(f"Your queue has popped! Please vote for a campaign in {channel_mention}")
            except discord.errors.Forbidden:
                print(f"Failed to send a DM to {participant.name}#{participant.discriminator}. DMs may be disabled for this user.")

    except asyncio.TimeoutError:
        pass  # Timeout is expected, no need to print an error
    
    await decrement_timeout()
    await voting(ctx, queue_type)

@bot.command()
async def mapdata(ctx):
    message = "```"
    
    with open('maps/campaign_maps.json', 'r') as file:
        vanilla_maps_data = json.load(file)
        message += "Vanilla Maps:\n"
        for map_info in vanilla_maps_data['maps']:
            if(map_info['timeout'] == 0):
                message += f"Map: {map_info['name']}, Timeout: {map_info['timeout']}, Play Count: {map_info['amountPlayed']}\n"

    with open('maps/custom_maps.json', 'r') as file:
        custom_maps_data = json.load(file)
        message += "Custom Maps:\n"
        for map_info in custom_maps_data['maps']:
            if(map_info['timeout'] == 0):
                message += f"Map: {map_info['name']}, Timeout: {map_info['timeout']}\n"
    
    message += "```"
    await ctx.send(message)

bot.run("MTE5ODQ1NDEzMjU1NDYwNDY3NA.G1IKNK.BCvewoHNRkcAp2E8NVGi3B4h_mxIC9Wd2Nachk")
