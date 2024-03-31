import sqlite3

# Function to create the necessary tables
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
    
    # Add games_played column if it doesn't exist
    cursor.execute("PRAGMA table_info(player)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'games_played' not in columns:
        cursor.execute('ALTER TABLE player ADD COLUMN games_played INTEGER NOT NULL DEFAULT 0')
    
    conn.commit()
    conn.close()

# Call create_tables() to ensure tables are created
if __name__ == "__main__":
    create_tables()
    print("Tables updated successfully.")