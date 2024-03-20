import discord
from discord.ext import commands
import random
import asyncio
import os
import json

from dotenv import load_dotenv

intents = discord.Intents.all()
intents.members = True
intents.reactions = True

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = 1072065028049600512
zeuskriegID = "1148387726719189103"

queue_in_progress = False
canSub = False

emoji_ids = {
    '1_Vanilla': 984524490191011860,
    '2_Vanilla': 984524491768098856,
    '3_Vanilla': 984524493932363867,
    '1_Custom': 984524488538460221,
    '2_Custom': 984525317672669264,
    '3_Custom': 984524493336752128,
    'Left_4_Dead': 984524530632491058,
}

bot = commands.Bot(command_prefix='!', intents=intents)

reacted_users = {
    'queue': set(),
    'sub': set()
}

queue_channel_id = None
queue_message = None
queued_players = []
voting_in_progress = False

participants_names = []

with open('campaign_maps.json', 'r') as file:
    vanilla_maps_data = json.load(file)

with open('custom_maps.json', 'r') as file:
    custom_maps_data = json.load(file)

async def decrement_timeout():
    global vanilla_maps_data, custom_maps_data
    
    for map_info in vanilla_maps_data['maps']:
        if map_info['timeout'] > 0:
            map_info['timeout'] -= 1
            if map_info['timeout'] < 0:
                map_info['timeout'] = 0

    with open('campaign_maps.json', 'w') as file:
        json.dump(vanilla_maps_data, file, indent=4)

    for map_info in custom_maps_data['maps']:
        if map_info['timeout'] > 0:
            map_info['timeout'] -= 1
            if map_info['timeout'] < 0:
                map_info['timeout'] = 0

    with open('custom_maps.json', 'w') as file:
        json.dump(custom_maps_data, file, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Try !queue standard"))

@bot.command()
async def queue(ctx):
    global queue_channel_id, queue_message, queued_players
    if queue_channel_id is not None:
        await ctx.send("Queue is already active!")
        return

    queue_channel_id = ctx.channel.id
    queue_message = await ctx.send("React with ✅ to join the queue!")
    queued_players = []

@bot.event
async def on_reaction_add(reaction, user):
    global queue_channel_id, queue_message, queued_players, voting_in_progress
    if voting_in_progress:
        return

    if queue_message and reaction.message.id == queue_message.id and str(reaction.emoji) == '✅':
        if user.id not in queued_players:
            queued_players.append(user.id)
            await reaction.message.channel.send(f"{user.mention} has joined the queue.")
        
        if len(queued_players) >= 2:
            await voting(reaction.message.channel, "some_queue_type")
            voting_in_progress = True

@bot.event
async def on_reaction_remove(reaction, user):
    global queue_channel_id, queue_message, queued_players
    if reaction.message.id == queue_message.id and str(reaction.emoji) == '✅':
        if user.id in queued_players:
            queued_players.remove(user.id)
            await reaction.message.channel.send(f"{user.mention} has left the queue.")

async def voting(ctx, queue_type):
    global participants_names, voting_in_progress

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
            return user.id != bot.user.id and str(reaction.emoji) in reactions


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
        with open('campaign_maps.json', 'w') as file:
            json.dump(available_vanilla_maps, file, indent=4)
    elif most_voted_map_type == "custom":
        with open('custom_maps.json', 'w') as file:
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
        f"Please join Pre-Game VC within 5 minutes or you may be subbed out.\n\n"
        f"`Survivors`\n{team1_mentions}\n\n"
        f"`Infected`\n{team2_mentions}\n\n"
        f"`=========`\n\n"
        f"**__This queue is live. Use the !finalize command to end this queue.__**\n\n"
        f"Use !sub to substitute players who don't show up. Substitute any applicable players before finalizing a queue.\n\n"
        f"*Please remember to send a Post-Game Summary before starting a new queue!*"
    )

    voting_in_progress = False

@bot.command()
async def command(ctx):
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
- !end: End the current queue and assign teams.
- !mapdata: Display map data.
- !help: Show this help message.
""", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def sub(ctx, player_to_remove: discord.Member, player_to_add: discord.Member):
    global participants_names

    if not canSub:
        await ctx.send("Teams have not been made yet.")
        return

    if player_to_add.name in participants_names:
        await ctx.send(f"{player_to_add.name} is already in the queue.")
        return

    if player_to_remove.name not in participants_names:
        await ctx.send(f"{player_to_remove.name} is not in the queue.")
        return

    participants_names.remove(player_to_remove.name)
    participants_names.append(player_to_add.name)

    await ctx.send(f"Substitution successful: {player_to_remove.name} replaced by {player_to_add.name}")

@bot.command()
async def mapdata(ctx):
    global vanilla_maps_data, custom_maps_data

    vanilla_maps_info = ""
    for map_info in vanilla_maps_data['maps']:
        map_name = map_info['name']
        map_votes = map_info['votes']
        map_timeout = map_info['timeout']
        vanilla_maps_info += f"{map_name}: Votes - {map_votes}, Timeout - {map_timeout}\n"

    custom_maps_info = ""
    for map_info in custom_maps_data['maps']:
        map_name = map_info['name']
        map_votes = map_info['votes']
        map_timeout = map_info['timeout']
        custom_maps_info += f"{map_name}: Votes - {map_votes}, Timeout - {map_timeout}\n"

    embed = discord.Embed(title="Map Data", color=0x00ff00)
    embed.add_field(name="Vanilla Maps", value=vanilla_maps_info, inline=False)
    embed.add_field(name="Custom Maps", value=custom_maps_info, inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def end(ctx):
    global queue_channel_id, queue_message, queued_players, participants_names, canSub

    if not queue_message or ctx.channel.id != queue_channel_id:
        await ctx.send("No active queue in this channel.")
        return

    canSub = True

    if len(queued_players) < 4:
        await ctx.send("Not enough players to create teams.")
        return

    random.shuffle(queued_players)
    participants_names = [str(await bot.fetch_user(player_id)) for player_id in queued_players]

    team1 = participants_names[:len(participants_names) // 2]
    team2 = participants_names[len(participants_names) // 2:]

    team1_str = "\n".join(team1)
    team2_str = "\n".join(team2)

    embed = discord.Embed(title="Teams", color=0x00ff00)
    embed.add_field(name="Team 1", value=team1_str, inline=False)
    embed.add_field(name="Team 2", value=team2_str, inline=False)

    await ctx.send(embed=embed)

    queue_channel_id = None
    queue_message = None
    queued_players = []
    canSub = False

@bot.command()
async def start(ctx):
    global queue_in_progress

    if queue_in_progress:
        await ctx.send("Queue is already in progress.")
        return

    queue_in_progress = True
    await ctx.send("Queue is now in progress.")

@bot.command()
async def stop(ctx):
    global queue_in_progress

    if not queue_in_progress:
        await ctx.send("No queue is currently in progress.")
        return

    queue_in_progress = False
    await ctx.send("Queue has been stopped.")

@bot.command()
async def reset(ctx):
    global queue_in_progress, participants_names, canSub

    queue_in_progress = False
    participants_names = []
    canSub = False

    await ctx.send("Queue has been reset.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Invalid command. Use !help for a list of commands.")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    if "dakki" in message.content.lower():
        await message.channel.send("Dakki is the greatest!")
    elif "krieg" in message.content.lower():
        await message.channel.send("Krieg is the ultimate gaming machine!")

    await asyncio.sleep(1)
    await decrement_timeout()

bot.run(BOT_TOKEN)
