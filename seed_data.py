import sqlite3
from utils.db_connection import get_connection

def seed_database():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON;")

        # ---------------------------------------------------------
        # 1. CREATE TABLES (IF THEY DO NOT EXIST)
        # ---------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT UNIQUE,
                country TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS venues (
                venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_name TEXT UNIQUE,
                city TEXT,
                country TEXT,
                capacity INTEGER
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT UNIQUE,
                team_id INTEGER,
                role TEXT,
                batting_style TEXT,
                bowling_style TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_name TEXT,
                match_description TEXT,
                team1_id INTEGER,
                team2_id INTEGER,
                winner_team_id INTEGER,
                margin INTEGER,
                margin_type TEXT,
                toss_winner_id INTEGER,
                toss_decision TEXT,
                venue_id INTEGER,
                match_date TEXT,
                format TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batting_performances (
                performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                player_id INTEGER,
                runs_scored INTEGER,
                balls_faced INTEGER,
                fours INTEGER,
                sixes INTEGER,
                dismissal_status TEXT,
                batting_position INTEGER,
                year INTEGER,
                quarter INTEGER
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bowling_performances (
                bowling_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                player_id INTEGER,
                overs_bowled REAL,
                runs_conceded INTEGER,
                wickets_taken INTEGER,
                economy_rate REAL,
                year INTEGER,
                quarter INTEGER
            );
        """)

        # ---------------------------------------------------------
        # 2. AUTO-MIGRATE ALL TABLES
        # ---------------------------------------------------------
        # Players Table
        existing_players_cols = [row[1] for row in cursor.execute("PRAGMA table_info(players);").fetchall()]
        if 'batting_style' not in existing_players_cols:
            cursor.execute("ALTER TABLE players ADD COLUMN batting_style TEXT;")
        if 'bowling_style' not in existing_players_cols:
            cursor.execute("ALTER TABLE players ADD COLUMN bowling_style TEXT;")

        # Teams Table
        existing_teams_cols = [row[1] for row in cursor.execute("PRAGMA table_info(teams);").fetchall()]
        if 'country' not in existing_teams_cols:
            cursor.execute("ALTER TABLE teams ADD COLUMN country TEXT;")

        # Batting Performances Table
        existing_batting_cols = [row[1] for row in cursor.execute("PRAGMA table_info(batting_performances);").fetchall()]
        if 'dismissal_status' not in existing_batting_cols:
            cursor.execute("ALTER TABLE batting_performances ADD COLUMN dismissal_status TEXT;")
        if 'batting_position' not in existing_batting_cols:
            cursor.execute("ALTER TABLE batting_performances ADD COLUMN batting_position INTEGER;")
        if 'match_id' not in existing_batting_cols:
            cursor.execute("ALTER TABLE batting_performances ADD COLUMN match_id INTEGER;")
        if 'year' not in existing_batting_cols:
            cursor.execute("ALTER TABLE batting_performances ADD COLUMN year INTEGER;")
        if 'quarter' not in existing_batting_cols:
            cursor.execute("ALTER TABLE batting_performances ADD COLUMN quarter INTEGER;")

        # Bowling Performances Table
        existing_bowling_cols = [row[1] for row in cursor.execute("PRAGMA table_info(bowling_performances);").fetchall()]
        if 'match_id' not in existing_bowling_cols:
            cursor.execute("ALTER TABLE bowling_performances ADD COLUMN match_id INTEGER;")
        if 'year' not in existing_bowling_cols:
            cursor.execute("ALTER TABLE bowling_performances ADD COLUMN year INTEGER;")
        if 'quarter' not in existing_bowling_cols:
            cursor.execute("ALTER TABLE bowling_performances ADD COLUMN quarter INTEGER;")

        # ---------------------------------------------------------
        # 3. DATA SEEDING
        # ---------------------------------------------------------
        teams = [('India', 'India'), ('Australia', 'Australia'), ('England', 'England'), ('South Africa', 'South Africa')]
        cursor.executemany("INSERT OR IGNORE INTO teams (team_name, country) VALUES (?, ?)", teams)

        venues = [
            ('Narendra Modi Stadium', 'Ahmedabad', 'India', 132000),
            ('Wankhede Stadium', 'Mumbai', 'India', 33000),
            ('Melbourne Cricket Ground', 'Melbourne', 'Australia', 100024),
            ('Lord\'s', 'London', 'England', 31180)
        ]
        cursor.executemany("INSERT OR IGNORE INTO venues (venue_name, city, country, capacity) VALUES (?, ?, ?, ?)", venues)

        players = [
            ('Virat Kohli', 1, 'Batsman', 'Right-hand bat', 'Right-arm medium'),
            ('Rohit Sharma', 1, 'Batsman', 'Right-hand bat', 'Right-arm offbreak'),
            ('Hardik Pandya', 1, 'All-rounder', 'Right-hand bat', 'Right-arm fast-medium'),
            ('Jasprit Bumrah', 1, 'Bowler', 'Right-hand bat', 'Right-arm fast'),
            ('Steve Smith', 2, 'Batsman', 'Right-hand bat', 'Right-arm legbreak'),
            ('Pat Cummins', 2, 'Bowler', 'Right-hand bat', 'Right-arm fast'),
            ('Joe Root', 3, 'Batsman', 'Right-hand bat', 'Right-arm offbreak'),
            ('Kagiso Rabada', 4, 'Bowler', 'Left-hand bat', 'Right-arm fast')
        ]
        cursor.executemany("INSERT OR IGNORE INTO players (player_name, team_id, role, batting_style, bowling_style) VALUES (?, ?, ?, ?, ?)", players)

        matches = [
            ('ICC World Cup 2023', 'IND vs AUS Final', 1, 2, 2, 6, 'wickets', 2, 'bowl', 1, '2023-11-19', 'ODI'),
            ('India vs England 2024', 'IND vs ENG 1st Test', 1, 3, 3, 28, 'runs', 1, 'bat', 2, '2024-01-25', 'Test'),
            ('Australia tour of SA 2023', 'SA vs AUS 1st ODI', 4, 2, 4, 111, 'runs', 2, 'bowl', 4, '2023-09-07', 'ODI')
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO matches 
            (series_name, match_description, team1_id, team2_id, winner_team_id, margin, margin_type, toss_winner_id, toss_decision, venue_id, match_date, format)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, matches)

        batting = [
            (1, 1, 185, 183, 12, 4, 'out', 3, 2023, 4),
            (1, 2, 141, 95, 12, 9, 'out', 1, 2023, 4),
            (1, 3, 45, 30, 4, 2, 'not out', 6, 2023, 4),
            (1, 4, 12, 15, 1, 0, 'out', 10, 2023, 4),
            (1, 5, 411, 330, 45, 12, 'out', 3, 2023, 4),
            (2, 6, 28, 35, 2, 1, 'out', 8, 2024, 1),
            (2, 7, 366, 420, 30, 3, 'out', 4, 2024, 1),
            (3, 8, 15, 20, 1, 0, 'out', 9, 2023, 3)
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO batting_performances 
            (match_id, player_id, runs_scored, balls_faced, fours, sixes, dismissal_status, batting_position, year, quarter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batting)

        bowling = [
            (1, 4, 9.0, 43, 2, 4.77, 2023, 4),
            (1, 6, 10.0, 34, 2, 3.40, 2023, 4),
            (2, 4, 15.0, 55, 4, 3.66, 2024, 1),
            (3, 8, 8.0, 41, 3, 5.12, 2023, 3)
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO bowling_performances 
            (match_id, player_id, overs_bowled, runs_conceded, wickets_taken, economy_rate, year, quarter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, bowling)

        conn.commit()
    finally:
        conn.close()

    print("Database schema successfully synchronized and seeded with complete player stats!")

if __name__ == '__main__':
    seed_database()

def reset_and_clean_players():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Clear existing duplicate/incomplete player records
        cursor.execute("DELETE FROM players;")
        
        # Reset SQLite Auto-increment counter for players table
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='players';")

        players = [
            ('Virat Kohli', 1, 'Batsman', 'Right-hand bat', 'Right-arm medium'),
            ('Rohit Sharma', 1, 'Batsman', 'Right-hand bat', 'Right-arm offbreak'),
            ('Hardik Pandya', 1, 'All-rounder', 'Right-hand bat', 'Right-arm fast-medium'),
            ('Jasprit Bumrah', 1, 'Bowler', 'Right-hand bat', 'Right-arm fast'),
            ('Steve Smith', 2, 'Batsman', 'Right-hand bat', 'Right-arm legbreak'),
            ('Pat Cummins', 2, 'Bowler', 'Right-hand bat', 'Right-arm fast'),
            ('Joe Root', 3, 'Batsman', 'Right-hand bat', 'Right-arm offbreak'),
            ('Kagiso Rabada', 4, 'Bowler', 'Left-hand bat', 'Right-arm fast')
        ]

        cursor.executemany("""
            INSERT INTO players (player_name, team_id, role, batting_style, bowling_style)
            VALUES (?, ?, ?, ?, ?)
        """, players)

        conn.commit()
        print("Successfully cleaned up duplicate entries and populated full style attributes!")
    finally:
        conn.close()

if __name__ == '__main__':
    reset_and_clean_players()