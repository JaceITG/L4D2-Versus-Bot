import discord
from discord.ext import commands

from database import add_or_update_player

### Queue ###
#
# status indicating state of Queue:
# 0 -> created, no announcement made
# 1 -> announced, waiting for joins
# 2 -> queue popped, waiting for map votes
# 3 -> game in progress
# 4 -> game ended, results logged

class Queue:

    def __init__(self, q_id: int, q_channel: discord.TextChannel, game_type: str):
        self.q_id = q_id
        self.game_type = game_type

        self.announcement_msg = ""
        self.status = 0
        
        self.players = []
        self.team1 = []
        self.team2 = []
        

    async def handle_reaction():
        pass

    # Record data from scores [team1, team2]
    async def log_match(scores):
        pass