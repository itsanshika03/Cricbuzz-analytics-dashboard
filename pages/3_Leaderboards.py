import sys
import importlib
import textwrap
from pathlib import Path
import streamlit as st
import pandas as pd
import sqlite3

# Force project root directory into sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import modules
import utils.ui
import utils.db_connection
importlib.reload(utils.ui)
importlib.reload(utils.db_connection)

from utils.ui import apply_global_cricbuzz_theme, render_sidebar_header, render_sidebar_footer
from utils.db_connection import get_db_connection

# Page Setup
st.set_page_config(
    page_title="Top Stats | Cricbuzz LiveStats",
    page_icon="🏆",
    layout="wide"
)

apply_global_cricbuzz_theme()

st.title("🏆 Top Player Statistics")
st.caption("Leaderboards, player rankings, and historical career performance metrics")

# ============================================================
# DATABASE INITIALIZATION & SEED HELPER
# ============================================================

def initialize_database():
    """Ensure database tables exist and are populated if missing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if missing
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            short_name TEXT
        );

        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            player_name TEXT NOT NULL,
            role TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS batting_performances (
            perf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            runs_scored INTEGER DEFAULT 0,
            balls_faced INTEGER DEFAULT 0,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        );
    """)

    # Seed initial data if players table is empty
    cursor.execute("SELECT COUNT(*) FROM players;")
    if cursor.fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO teams (team_id, team_name, short_name) VALUES 
            (1, 'India', 'IND'),
            (2, 'Australia', 'AUS'),
            (3, 'England', 'ENG'),
            (4, 'South Africa', 'RSA');

            INSERT INTO players (player_id, team_id, player_name, role) VALUES 
            (1, 1, 'Virat Kohli', 'Batsman'),
            (2, 1, 'Rohit Sharma', 'Batsman'),
            (3, 2, 'Steve Smith', 'Batsman'),
            (4, 2, 'Travis Head', 'All-Rounder'),
            (5, 3, 'Joe Root', 'Batsman'),
            (6, 4, 'Kagiso Rabada', 'Bowler');

            INSERT INTO batting_performances (player_id, runs_scored, balls_faced, fours, sixes) VALUES 
            (1, 8850, 6200, 810, 145),
            (2, 7920, 5800, 750, 190),
            (3, 7210, 6100, 680, 55),
            (4, 4350, 3100, 420, 98),
            (5, 8100, 7500, 790, 42);
        """)
        conn.commit()
    conn.close()

# Run initialization safeguard
try:
    initialize_database()
except Exception as e:
    st.warning(f"Note on DB Init: {e}")

# ============================================================
# FETCH STATS DATA
# ============================================================

def get_top_run_scorers():
    conn = get_db_connection()
    query = """
    SELECT 
        p.player_name AS 'Player Name',
        t.team_name AS 'Team',
        p.role AS 'Role',
        COALESCE(SUM(bp.runs_scored), 0) AS 'Total Runs',
        COALESCE(SUM(bp.fours), 0) AS 'Fours',
        COALESCE(SUM(bp.sixes), 0) AS 'Sixes'
    FROM players p
    LEFT JOIN teams t ON p.team_id = t.team_id
    LEFT JOIN batting_performances bp ON p.player_id = bp.player_id
    GROUP BY p.player_id, p.player_name, t.team_name, p.role
    ORDER BY 'Total Runs' DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ============================================================
# RENDER LEADERBOARDS
# ============================================================

st.markdown(
    textwrap.dedent("""
    <div class="dashboard-card" style="margin-bottom: 20px;">
        <div class="section-title">🥇 Top Run Scorers</div>
        <div class="section-subtitle">Aggregated career & series runs from SQLite database</div>
    </div>
    """),
    unsafe_allow_html=True
)

try:
    top_scorers_df = get_top_run_scorers()
    
    if not top_scorers_df.empty:
        st.dataframe(
            top_scorers_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No player performance records found in database.")
        
except Exception as err:
    st.error(f"Error executing statistics query: {err}")