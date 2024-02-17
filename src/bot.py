import discord
from discord.ext import commands
import random
import asyncio

# Define the intents
intents = discord.Intents.all()
intents.members = True
intents.reactions = True

zeuskriegID = "1148387726719189103"
retardedLPID = 317412117240348675


bot = commands.Bot(command_prefix='!', intents=intents)
padicia = bot.get_user(retardedLPID)

# Dictionary to store users who have reacted
reacted_users = {
    'queue': set(),
    'sub': set()
}

# List to store participants' names
participants_names = []

# Read campaign maps from the text file
with open('maps/campaign_maps.txt', 'r') as file:
    campaign_maps = [line.strip() for line in file]

# Read custom maps from the text file
with open('maps/custom_maps.txt', 'r') as file:
    custom_maps = [line.strip() for line in file]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Try !queue standard"))

# Command to join the queue, start map vote, and assign teams
@bot.command()
async def queue(ctx, queue_type):
    allowed_role = discord.utils.get(ctx.guild.roles, name='Matchmaker')
    if allowed_role in ctx.author.roles:
        # Proceed with the queue process if the user has the allowed role
        await queue_process(ctx, queue_type)
    else:
        with open('coach.jpg', 'rb') as file:
            image = discord.File(file)
        await ctx.send(file=image)
        await ctx.send("Shut the fuck up.")

# Command to manually start map voting
@bot.command()
async def start_voting(ctx):
    await voting(ctx)

# Function to start map voting
async def voting(ctx):
    global participants_names, reacted_users

    selected_campaigns = random.sample(campaign_maps, 3)
    selected_customs = random.sample(custom_maps, 3)

    vote_message = (
        f"Vote for the campaign you'd like to play! The campaign with the most votes wins. Tied campaigns will be chosen at random.\n\n"
        f"`=== Vanilla Campaigns ===`\n"
        f"1. {selected_campaigns[0]}\n"
        f"2. {selected_campaigns[1]}\n"
        f"3. {selected_campaigns[2]}\n\n"
        f"`=== Custom Campaigns ===`\n"
        f"4. {selected_customs[0]}\n"
        f"5. {selected_customs[1]}\n"
        f"6. {selected_customs[2]}\n\n"
        f"7. Reroll the maps\n"
        f"Missing our custom campaigns? Download them here: <https://steamcommunity.com/sharedfiles/filedetails/?id=3023799326>"
    )

    vote_msg = await ctx.send(vote_message)

    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']  # Added a reroll option

    # Function to check if the reaction is from the author and not the bot
    def check_reaction(reaction, user):
        return user == ctx.author and str(reaction.emoji) in reactions and user != ctx.bot.user

    for reaction in reactions:
        await vote_msg.add_reaction(reaction)

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check_reaction)
        except asyncio.TimeoutError:
            break  # Timeout, end the voting

    index = reactions.index(str(reaction.emoji))

    # If reroll option is chosen
    if index == 6:
        await ctx.send("Rerolling maps...")
        await voting(ctx)  # Restart the voting process
        return

    if index < 3:
        most_voted_map = selected_campaigns[index]
    elif 3 <= index < 6:
        most_voted_map = selected_customs[index - 3]
    else:
        await ctx.send("Invalid vote index.")
        return


    # Attempt to create balanced teams
    balanced_teams = False
    while not balanced_teams:
        # Shuffle participants list and divide into teams
        random.shuffle(participants_names)
        team_size = len(participants_names) // 2
        team1_names = participants_names[:team_size]
        team2_names = participants_names[team_size:]

        # Check if the teams are balanced
        if abs(len(team1_names) - len(team2_names)) <= 1:
            balanced_teams = True

    # Notify all players about the teams with mentions
    team1_mentions = '\n'.join([f'<@{ctx.guild.get_member_named(name).id}>' for name in team1_names])
    team2_mentions = '\n'.join([f'<@{ctx.guild.get_member_named(name).id}>' for name in team2_names])

    # Print the specified output
    await ctx.send(
        f"**{most_voted_map}** has won and teams have been assigned! "
        f"Please join Pre-Game VC within 10 minutes or you may be subbed out.\n\n"
        f"`Survivors`\n{team1_mentions}\n\n"
        f"`Infected`\n{team2_mentions}\n\n"
    )
    
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
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'realism': (
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Realism__** is being set up for 8 players!\n"
            "(Survivors can't see player or item outlines; common infected are more resilient; Witches kill instantly!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'survival':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Survival__** versus game is being set up for 8 players!\n"
            "(Survivors hold out in a small arena; teams swap; the Survivor team with the longest time alive wins!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'jockey':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Riding My Survivor__** versus game is being set up for 8 players!\n"
            "(Jockeys are the only Special Infected; Jockey HP, DMG, and speed are significantly increased!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'scavenge':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Scavenge__** versus game is being set up for 8 players!\n"
            "(Survivors collect gas cans in a small arena; teams swap; the Survivor team with the most gas cans wins!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'bleed':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Bleed Out__** versus game is being set up for 8 players!\n"
            "(Survivors only have temporary HP; First Aid Kits are replaced with Adrenaline and Pain Pills!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'tank':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Taaannnkk!__** versus game is being set up for 8 players!\n"
            "(Only Tanks spawn; First Aid Kits are replaced with Adrenaline and Pain Pills!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'hpack':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Healthpackalypse!__** versus game is being set up for 8 players!\n"
            "(All health items are removed from spawn pools!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
            "Once 8 players have reacted, maps will be voted upon, and teams will be assigned.\n"
            "Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you have at least two hours available.**\n\n"
            f"Please report any issues to {zeusMention}"
        ),
        'confogl':(
            f"{carriers_role.mention} {ksobs_role.mention}\n" 
            "A **__Confogl__** versus game is being set up for 8 players!\n"
            "(First Aid Kits are removed; more Adrenaline and Pain Pills spawn; only Tier-1 weapons!)\n\n"
            "To join the queue, react to this message with ✅\n"
            "To join as a sub, react to this message with :Substitute:\n\n"
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
            "To join as a sub, react to this message with :Substitute:\n\n"
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
            "To join as a sub, react to this message with :Substitute:\n\n"
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
    await queue_msg.add_reaction("❌")

    def check(reaction, user):
        return (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌") and user != bot.user

    try:
        while len(reacted_users['queue']) < 8:
            reaction, user = await bot.wait_for('reaction_add', timeout=None, check=check)

            if str(reaction.emoji) == "✅":
                reacted_users['queue'].add(user.id)
                participants_names.append(user.name)
            elif str(reaction.emoji) == "❌":
                reacted_users['sub'].add(user.id)

        for participant_id in reacted_users['queue']:
            participant = await ctx.guild.fetch_member(participant_id)

            try:
                await participant.send("The queue has reached 8 players. Maps will now be voted upon!")
            except discord.errors.Forbidden:
                print(f"Failed to send a DM to {participant.name}#{participant.discriminator}. DMs may be disabled for this user.")

    except asyncio.TimeoutError:
        pass  # Timeout is expected, no need to print an error

    await voting(ctx)

# Run the bot
bot.run('MTE5ODQ1NDEzMjU1NDYwNDY3NA.GmWW2N.TLllhu77J2sQRsbhBJZ1MW_imPf4i-MzMZDaB0')
