import discord
from discord.ext import commands
import random
import asyncio
import os
from datetime import datetime
import json
from database import create_tables, add_or_update_player, get_top_players, get_player_stats

from dotenv import load_dotenv
intents = discord.Intents.all()
intents.members = True
intents.reactions = True

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = 1072065028049600512
zeuskriegID = "1148387726719189103"

emoji_ids = {
    '1_Vanilla': 984524490191011860,
    '2_Vanilla': 1211013201081405490,
    '3_Vanilla': 984524493932363867,
    '1_Custom': 984524488538460221,
    '2_Custom': 1211013204382195753,
    '3_Custom': 984524493336752128,
    'Left_4_Dead': 984524530632491058,
}


bot = commands.Bot(command_prefix='!', intents=intents)
queue_channel_id = None
queued_players = []
voting_in_progress = False

canUnreact = True

gameInProgress = False

queue_in_progress = False
canSub = False

team1_names = []
team2_names = []

teamsHaveBeenMade = False
canUseVotingCommand = False
queueIsFull = False

with open('campaign_maps.json', 'r') as file:
    vanilla_maps_data = json.load(file)

with open('custom_maps.json', 'r') as file:
    custom_maps_data = json.load(file)

async def decrement_timeout():
    # Load and update vanilla maps
    with open('campaign_maps.json', 'r') as file:
        vanilla_maps_data = json.load(file)
        for map_info in vanilla_maps_data['maps']:
            if map_info['timeout'] > 0:
                map_info['timeout'] -= 1
                if map_info['timeout'] < 0:
                    map_info['timeout'] = 0

    # Write updated vanilla maps data back to JSON file
    with open('campaign_maps.json', 'w') as file:
        json.dump(vanilla_maps_data, file, indent=4)

    # Load and update custom maps
    with open('custom_maps.json', 'r') as file:
        custom_maps_data = json.load(file)
        for map_info in custom_maps_data['maps']:
            if map_info['timeout'] > 0:
                map_info['timeout'] -= 1
                if map_info['timeout'] < 0:
                    map_info['timeout'] = 0

    # Write updated custom maps data back to JSON file
    with open('custom_maps.json', 'w') as file:
        json.dump(custom_maps_data, file, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Try !queue standard"))

@bot.command()
async def queue(ctx, queue_type):
    global queue_channel_id, queued_players, queue_msg, canUnreact
    if queue_channel_id is not None:
        await ctx.send("Queue is already active!")
        return

    carriers_role = discord.utils.get(ctx.guild.roles, name='Carriers')
    ksobs_role = discord.utils.get(ctx.guild.roles, name='Kill All SOBs!')
    
    zeusMention = f'<@{zeuskriegID}>'

    queue_channel_id = ctx.channel.id

    await ctx.message.delete()

    # Generate a queue message for the chosen game mode
    def queue_message(gamemode):
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


    # Send the appropriate queue information message
    try:
        queue_msg = await ctx.send(queue_message(queue_type), delete_after=None)
    except ValueError:
        await ctx.send("Invalid queue type. Available types: standard, custom")
        return

    await queue_msg.add_reaction("✅")
    await queue_msg.add_reaction("<:Substitute:984524545866219631>")

    canUnreact = True

@bot.event
async def on_reaction_add(reaction, user):
    global queue_msg, queued_players, voting_in_progress, canUnreact, canUseVotingCommand, queueIsFull, queue_in_progress, teamsHaveBeenMade
    
    if queue_msg is None or queue_in_progress or voting_in_progress:
        return

    if str(reaction.emoji) == '✅' and user != bot.user and reaction.message.id == queue_msg.id:
        if user.id not in queued_players:
            queued_players.append(user.id)
            print(queued_players)

        if len(queued_players) >= 8:
            canUnreact = False
            if not queue_in_progress:
                await notify()
                queue_in_progress = True
                queueIsFull = True

@bot.event
async def on_reaction_remove(reaction, user):
    global queue_msg, queued_players, canUnreact

    if queue_msg is None or not canUnreact:
        return

    if str(reaction.emoji) == '✅' and reaction.message.id == queue_msg.id:
        if user.id in queued_players:
            queued_players.remove(user.id)
            print(queued_players)

async def notify():
    global queued_players, canUseVotingCommand
    for player_id in queued_players[:8]:
        player = await bot.fetch_user(player_id)
        if player:
            queue_channel = bot.get_channel(1072065028049600512)
            if queue_channel:
                queue_channel_link = queue_channel.mention
                await player.send(f"The queue has reached 8 players! Please join Pre-Game VC and be ready to vote! {queue_channel_link}.")
            else:
                await player.send("The queue has reached 8 players! Please join Pre-Game VC and be ready to vote!")
    
    canUseVotingCommand = True  # Allow voting command to be used after the queue has popped


@bot.command()
async def voting(ctx):
    global queue_in_progress, team1_names, team2_names, canSub, most_voted_map, voting_in_progress, queued_players, teamsHaveBeenMade, canUseVotingCommand

    if not queue_in_progress:
        await ctx.send("Voting is not available at the moment.")
        print("YEE")
        return
    
    if not canUseVotingCommand:
        await ctx.send("Voting is not available at the moment.")
        return

    canUseVotingCommand = False
    voting_in_progress = True

    with open('campaign_maps.json', 'r') as file:
        available_vanilla_maps = json.load(file)
        available_vanilla_maps_filtered = [map_info for map_info in available_vanilla_maps['maps'] if map_info['timeout'] == 0]
        selected_vanilla_maps = random.sample(available_vanilla_maps_filtered, min(3, len(available_vanilla_maps_filtered)))

    with open('custom_maps.json', 'r') as file:
        available_custom_maps = json.load(file)
        available_custom_maps_filtered = [map_info for map_info in available_custom_maps['maps'] if map_info['timeout'] == 0]
        selected_customs = random.sample(available_custom_maps_filtered, min(3, len(available_custom_maps_filtered)))

    vote_message = (
        f"Vote for the campaign you'd like to play! The campaign with the most votes wins. Tied campaigns will be chosen at random.\n\n"
        f"`=== Vanilla Campaigns ===`\n"
    )

    for i, map_name in enumerate(selected_vanilla_maps, start=1):
        vote_message += f"<:{i}_Vanilla:{emoji_ids[str(i)+'_Vanilla']}> —  {map_name['name']}\n"

    vote_message += f"\n"

    vote_message += "`=== Custom Campaigns ===`\n"
    for i, map_name in enumerate(selected_customs, start=1):
        vote_message += f"<:{i}_Custom:{emoji_ids[str(i)+'_Custom']}> —  {map_name['name']}\n"

    vote_message += (
        f"\n<:Left_4_Dead:{emoji_ids['Left_4_Dead']}> —  Reroll the maps\n"
        f"Missing our custom campaigns? Download them here: <https://steamcommunity.com/sharedfiles/filedetails/?id=3023799326>"
    )

    # Send the voting message
    vote_msg = await ctx.send(vote_message)

    # Add reactions to the voting message
    reactions = [f'<:{emoji_name}:{emoji_id}>' for emoji_name, emoji_id in emoji_ids.items()]

    def check_reaction(reaction, user):
        return user.id != bot.user.id and str(reaction.emoji) in reactions and reaction.message.id == vote_msg.id

    for reaction in reactions:
        await vote_msg.add_reaction(reaction)

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=25, check=check_reaction)
        except asyncio.TimeoutError:
            break  # Timeout, end the voting

        if reaction is None or user is None:
            break

    # Determine the most voted map
    index = reactions.index(str(reaction.emoji)) if reaction is not None else None
    if index == 6:
        discriminators = [map_info['name'] for map_info in selected_vanilla_maps + selected_customs]
        await revote(ctx, *discriminators)  # Pass the discriminators as arguments
        return
    if index is not None and index < 3:
        most_voted_map = selected_vanilla_maps[index]
        most_voted_map_type = "vanilla"
    elif index is not None and 3 <= index < 6:
        most_voted_map = selected_customs[index - 3]
        most_voted_map_type = "custom"
    else:
        await ctx.send("Invalid vote index.")
        return
    
    most_voted_map['timeout'] = 3
    most_voted_map['amountPlayed'] += 1

    if most_voted_map_type == "vanilla":
        with open('campaign_maps.json', 'w') as file:
            json.dump(available_vanilla_maps, file, indent=4)
    elif most_voted_map_type == "custom":
        with open('custom_maps.json', 'w') as file:
            json.dump(available_custom_maps, file, indent=4)

    balanced_teams = False
    while not balanced_teams:
        random.shuffle(queued_players)
        team_size = len(queued_players) // 2
        team1_names = queued_players[:team_size]
        team2_names = queued_players[team_size:]

        if abs(len(team1_names) - len(team2_names)) <= 1:
            balanced_teams = True
    # Construct team mentions
    team1_mentions = '\n'.join([f'<@{name}>' for name in team1_names])
    team2_mentions = '\n'.join([f'<@{name}>' for name in team2_names])

    # Send the message with the most voted map and assigned teams
    await ctx.send(
        f"**{most_voted_map['name']}** has won and teams have been assigned! "
        f"Please join Pre-Game VC within 5 minutes or you may be subbed out.\n\n"
        f"`Survivors`\n{team1_mentions}\n\n"
        f"`Infected`\n{team2_mentions}\n\n"
        f"`=========`\n\n"
        f"**__This queue is live. Use the !end *queue type* command to end this queue.__**\n\n"
        f"Use !sub to substitute players who don't show up. Substitute any applicable players before finalizing a queue.\n\n"
        f"*Please remember to send a Post-Game Summary before starting a new queue!*"
    )

    voting_in_progress = False
    canSub = True
    teamsHaveBeenMade = True


@bot.command()
async def revote(ctx, *discriminators):
    global queue_in_progress, team1_names, team2_names, canSub, most_voted_map, voting_in_progress, queued_players

    voting_in_progress = True

    with open('campaign_maps.json', 'r') as file:
        available_vanilla_maps = json.load(file)
        available_vanilla_maps_filtered = [map_info for map_info in available_vanilla_maps['maps'] if map_info['timeout'] == 0]
        # Exclude previously chosen maps
        selected_vanilla_maps = [map_info for map_info in available_vanilla_maps_filtered if map_info['name'] not in discriminators]
        selected_vanilla_maps = random.sample(selected_vanilla_maps, min(3, len(selected_vanilla_maps)))

    with open('custom_maps.json', 'r') as file:
        available_custom_maps = json.load(file)
        available_custom_maps_filtered = [map_info for map_info in available_custom_maps['maps'] if map_info['timeout'] == 0]
        # Exclude previously chosen maps
        selected_customs = [map_info for map_info in available_custom_maps_filtered if map_info['name'] not in discriminators]
        selected_customs = random.sample(selected_customs, min(3, len(selected_customs)))

    vote_message = (
        f"The maps have been re-rolled. You have a short period of time to vote for a different map.\n\n"
        f"`=== Vanilla Campaigns ===`\n"
    )

    for i, map_name in enumerate(selected_vanilla_maps, start=1):
        vote_message += f"<:{i}_Vanilla:{emoji_ids[str(i)+'_Vanilla']}> —  {map_name['name']}\n"

    vote_message += f"\n"

    vote_message += "`=== Custom Campaigns ===`\n"
    for i, map_name in enumerate(selected_customs, start=1):
        vote_message += f"<:{i}_Custom:{emoji_ids[str(i)+'_Custom']}> —  {map_name['name']}\n"
    
    vote_message += f"\n"

    vote_message += (
        f"Missing our custom campaigns? Download them here: <https://steamcommunity.com/sharedfiles/filedetails/?id=3023799326>"
    )

    # Send the voting message
    vote_msg = await ctx.send(vote_message)

    # Add reactions to the voting message
    reactions = [f'<:{emoji_name}:{emoji_id}>' for emoji_name, emoji_id in emoji_ids.items()]

    def check_reaction(reaction, user):
        return user.id != bot.user.id and str(reaction.emoji) in reactions and reaction.message.id == vote_msg.id

    for reaction in reactions:
        await vote_msg.add_reaction(reaction)

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30, check=check_reaction)
        except asyncio.TimeoutError:
            break  # Timeout, end the voting

        if reaction is None or user is None:
            break

    # Determine the most voted map
    index = reactions.index(str(reaction.emoji)) if reaction is not None else None
    if index is not None and index < 3:
        most_voted_map = selected_vanilla_maps[index]
        most_voted_map_type = "vanilla"
    elif index is not None and 3 <= index < 6:
        most_voted_map = selected_customs[index - 3]
        most_voted_map_type = "custom"
    else:
        await ctx.send("Invalid vote index.")
        return
    
    most_voted_map['timeout'] = 3
    most_voted_map['amountPlayed'] += 1

    if most_voted_map_type == "vanilla":
        with open('campaign_maps.json', 'w') as file:
            json.dump(available_vanilla_maps, file, indent=4)
    elif most_voted_map_type == "custom":
        with open('custom_maps.json', 'w') as file:
            json.dump(available_custom_maps, file, indent=4)

    balanced_teams = False
    while not balanced_teams:
        random.shuffle(queued_players)
        team_size = len(queued_players) // 2
        team1_names = queued_players[:team_size]
        team2_names = queued_players[team_size:]

        if abs(len(team1_names) - len(team2_names)) <= 1:
            balanced_teams = True

    # Construct team mentions
    team1_mentions = '\n'.join([f'<@{name}>' for name in team1_names])
    team2_mentions = '\n'.join([f'<@{name}>' for name in team2_names])

    # Send the message with the most voted map and assigned teams
    await ctx.send(
        f"**{most_voted_map['name']}** has won and teams have been assigned! "
        f"Please join Pre-Game VC within 5 minutes or you may be subbed out.\n\n"
        f"`Survivors`\n{team1_mentions}\n\n"
        f"`Infected`\n{team2_mentions}\n\n"
        f"`=========`\n\n"
        f"**__This queue is live. Use the !end *queue type* command to end this queue.__**\n\n"
        f"Use !sub to substitute players who don't show up. Substitute any applicable players before finalizing a queue.\n\n"
        f"*Please remember to send a Post-Game Summary before starting a new queue!*"
    )

    voting_in_progress = False
    teamsHaveBeenMade = True
    canSub = True

@bot.command()
async def jockey(ctx):
    embed = discord.Embed(title="Left 4 Dead 2 Queue Bot Help", color=0x00ff00)
    embed.add_field(name="Queue Types:", value=
"""
- !queue standard: Standard Vanilla+ Versus
- !queue realism: Realism Versus
- !queue survival: Survival Versus
- !queue jockey: Riding My Survivor Versus
- !queue scavenge: Scavenge Versus
- !queue bleed: Bleed Out Versus
- !queue tank: Taaannnkk! Versus
- !queue hpack: Healthpackalypse! Versus
- !queue confogl: Confogl Versus
- !queue l4d1: Left 4 Dead 1 Versus
- !queue l4d2: Unmodded L4D2 Versus
""", inline=False)
    
    embed.add_field(name="Commands:", value=
"""
- !queue [queue_type]: Start a new queue.
- !sub [player_to_remove] [player_to_add]: Substitute a player in the queue.
- !end [queue_type] [winning team]: End the current queue.
- !mapdata: Display map data.
- !jockey: Show this help message.
- !balance: [Player1] [Player2] switch players on opposite teams
""", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def sub(ctx, player_to_remove: discord.Member, player_to_add: discord.Member):
    global team1_names, team2_names, canSub, queued_players

    if not canSub:
        await ctx.send("Teams have not been made yet.")
        return

    # Check if the player to add is already in the queue
    if player_to_add.id in queued_players:
        await ctx.send(f"{player_to_add.display_name} is already in the queue.")
        return

    # Check if the player to remove is in the queue
    if player_to_remove.id not in queued_players:
        await ctx.send(f"{player_to_remove.display_name} is not in the queue.")
        return

    # Remove the player to remove and add the player to add
    if player_to_remove.id in team1_names:
        team1_names.remove(player_to_remove.id)
        team1_names.append(player_to_add.id)
    elif player_to_remove.id in team2_names:
        team2_names.remove(player_to_remove.id)
        team2_names.append(player_to_add.id)

    # Update participants_names
    queued_players.remove(player_to_remove.id)
    queued_players.append(player_to_add.id)

    # Construct team mentions
    team1_mentions = '\n'.join([f'<@{name}>' for name in team1_names])

    team2_mentions = '\n'.join([f'<@{name}>' for name in team2_names])

    # Send the updated teams message
    await ctx.send(
        f"**Updated Teams**:\n\n"
        f"`Survivors`\n{team1_mentions}\n\n"
        f"`Infected`\n{team2_mentions}\n\n"
    )


@bot.command()
async def end(ctx, queue_type, winning_team):
    global queue_channel_id, queue_msg, queued_players, canSub, canUnreact, most_voted_map, team1_names, team2_names, teamsHaveBeenMade, queueIsFull, queue_in_progress
    if queue_channel_id is None:
        await ctx.send("Queue is not active!")
        return

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    # Convert team names to strings
    team1_names = [str(name) for name in team1_names]
    team2_names = [str(name) for name in team2_names]

    # Fetch guild members to get their usernames
    guild = ctx.guild
    team1_usernames = []
    team2_usernames = []

    for member_id in team1_names:
        member = guild.get_member(int(member_id))
        if member:
            team1_usernames.append(member.display_name)

    for member_id in team2_names:
        member = guild.get_member(int(member_id))
        if member:
            team2_usernames.append(member.display_name)

    
    importantPeople = ["317412117240348675", "1148387726719189103"]

    if(winning_team != "none"):
        for user_id in importantPeople:
            user = await bot.fetch_user(user_id)  # No need to convert to string for user ID
            if user:
                try:
                    await user.send(
                        f"**__Queue Information__**\n\n"
                        f"**Date Popped**: {current_time}\n"
                        f"**Queue Type**: {queue_type.capitalize()}\n"
                        f"**Campaign**: {most_voted_map['name']}\n"
                        f"**Survivors**: {', '.join(team1_usernames)}\n"
                        f"**Infected**: {', '.join(team2_usernames)}\n"
                    )
                except Exception as e:
                    print(f"Failed to send queue info to user with ID {user_id}: {e}")
    
    

    # Update players' stats
    if winning_team.lower() == "infected":
        for player_name in team2_usernames:
            add_or_update_player(player_name, win=True)

        for player_name in team1_usernames:
            add_or_update_player(player_name, win=False)
    elif winning_team.lower() == "survivors":
        for player_name in team1_usernames:
            add_or_update_player(player_name, win=True)

        for player_name in team2_usernames:
            add_or_update_player(player_name, win=False)
    elif winning_team.lower() == "none":
        pass  # Do nothing, just end the queue without updating stats
    else:
        await ctx.send("Invalid winning team. Please choose 'survivors' or 'infected'.")

    # Reset all queue-related variables
    await decrement_timeout()
    canSub = False
    queue_msg = None
    queued_players = []
    queue_channel_id = None
    canUnreact = True
    teamsHaveBeenMade = False
    queue_in_progress = False
    await ctx.send("Queue has been ended.")

@bot.command()
async def balance(ctx, player1: discord.Member, player2: discord.Member):
    global queue_in_progress

    if not queue_in_progress:
        return
    
    if player1.id not in queued_players or player2.id not in queued_players:
        await ctx.send("Both players must be in the queue to switch teams.")
        return

    # Check if the players are on opposite teams
    team1_players = queued_players[:len(queued_players)//2]
    team2_players = queued_players[len(queued_players)//2:]
    
    if (player1.id in team1_players and player2.id in team1_players) or \
       (player1.id in team2_players and player2.id in team2_players):
        await ctx.send("Players must be on opposite teams to switch.")
        return

    # Switch the players in the queued_players list
    index_player1 = queued_players.index(player1.id)
    index_player2 = queued_players.index(player2.id)
    queued_players[index_player1], queued_players[index_player2] = queued_players[index_player2], queued_players[index_player1]

    # Construct team mentions
    team1_mentions = '\n'.join([f'<@{name}>' for name in queued_players[:len(queued_players)//2]])
    team2_mentions = '\n'.join([f'<@{name}>' for name in queued_players[len(queued_players)//2:]])

    # Send a message to confirm the team switch
    await ctx.send(
        "`Survivors`\n" + team1_mentions + "\n\n"
        "`Infected`\n" + team2_mentions
    )


@bot.command()
async def mapdata(ctx):
    message = "```"

    message += "Possible Vanilla Map Pool: \n"
    
    with open('campaign_maps.json', 'r') as file:
        vanilla_maps_data = json.load(file)
        for map_info in vanilla_maps_data['maps']:
            if(map_info['timeout'] == 0):
                message += f"Map: {map_info['name']}, Timeout: {map_info['timeout']}, Play Count: {map_info['amountPlayed']}\n"

    message += "Possible Custom Map Pool: \n"

    with open('custom_maps.json', 'r') as file:
        custom_maps_data = json.load(file)
        for map_info in custom_maps_data['maps']:
            if(map_info['timeout'] == 0):
                message += f"Map: {map_info['name']}, Timeout: {map_info['timeout']}\n"
    
    message += "```"
    await ctx.send(message)

@bot.command()
async def fuckserverrules(ctx):
    global queued_players, teamsHaveBeenMade

    if not (teamsHaveBeenMade):
        return 
    
    balanced_teams = False
    while not balanced_teams:
        random.shuffle(queued_players)
        team_size = len(queued_players) // 2
        team1_names = queued_players[:team_size]
        team2_names = queued_players[team_size:]

        if abs(len(team1_names) - len(team2_names)) <= 1:
            balanced_teams = True

    # Construct team mentions
    team1_mentions = '\n'.join([f'<@{name}>' for name in team1_names])
    team2_mentions = '\n'.join([f'<@{name}>' for name in team2_names])

    # Send the message with the assigned teams
    await ctx.send(
        "**FUCK SERVER RULES!**"
        "Teams have been reassigned!\n\n"
        "`Team 1`\n" + team1_mentions + "\n\n"
        "`Team 2`\n" + team2_mentions
    )

bot.run(BOT_TOKEN)