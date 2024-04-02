import sqlite3

def create_tables():
    conn = sqlite3.connect('player.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            games_played INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_player(player_id, win=False):
    with sqlite3.connect('player.db') as conn:
        cursor = conn.cursor()

        # Check if the player exists in the player table
        cursor.execute('SELECT * FROM player WHERE player_id = ?', (player_id,))
        existing_player = cursor.fetchone()

        if existing_player:
            # Player exists, update wins, losses, and games played
            if win:
                cursor.execute('UPDATE player SET wins = wins + 1, games_played = games_played + 1 WHERE player_id = ?', (player_id,))
            else:
                cursor.execute('UPDATE player SET losses = losses + 1, games_played = games_played + 1 WHERE player_id = ?', (player_id,))
        else:
            # Player does not exist, add them to player table
            cursor.execute('INSERT INTO player (player_id, wins, losses, games_played) VALUES (?, ?, ?, ?)', (player_id, int(win), int(not win), 1))

        conn.commit()

def get_top_players(n):
    with sqlite3.connect('player.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT player_id, wins, losses, games_played, (wins * 1.0 / (losses + 1)) AS score FROM player ORDER BY score DESC LIMIT ?', (n,))
        top_players = cursor.fetchall()
        return top_players
    
def get_player_stats(player_id):
    conn = sqlite3.connect('player.db')
    cursor = conn.cursor()
    cursor.execute('SELECT wins, losses, games_played FROM player WHERE player_id = ?', (player_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        stats = {
            'wins': result[0],
            'losses': result[1],
            'games_played': result[2]
        }
        return stats
    else:
        # If player not found, return default stats
        return {
            'wins': 0,
            'losses': 0,
            'games_played': 0
        }