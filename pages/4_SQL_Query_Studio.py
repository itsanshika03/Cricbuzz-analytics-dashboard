import sys
import importlib
from pathlib import Path
import streamlit as st
import pandas as pd

# Force project root directory into sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import utils.ui
import utils.db_connection
import utils.api_client

# Reload modules to pick up changes without restarting
importlib.reload(utils.ui)
importlib.reload(utils.db_connection)
importlib.reload(utils.api_client)

from utils.ui import apply_global_cricbuzz_theme, render_sidebar_header, render_sidebar_footer
from utils.db_connection import get_db_connection
from utils.api_client import get_live_team_names

# Page Configuration
st.set_page_config(
    page_title="SQL Analytics | LiveStats",
    page_icon="🏏",
    layout="wide"
)

# Apply Global Dashboard Theme
apply_global_cricbuzz_theme()

# --- Initialize DB Connection ---
conn = get_db_connection()

# --- Fetch Dynamic Live Teams from API ---
@st.cache_data(ttl=60)
def load_live_team_options():
    try:
        api_teams = get_live_team_names()
        if api_teams:
            return ["All"] + api_teams
    except Exception:
        pass
    
    # Fallback to DB teams if API returns no live matches or fails
    try:
        if conn:
            db_teams = pd.read_sql_query("SELECT team_name FROM teams ORDER BY team_name ASC", conn)["team_name"].tolist()
            if db_teams:
                return ["All"] + db_teams
    except Exception:
        pass

    return ["All", "India", "Australia", "England", "South Africa", "Pakistan"]

live_teams_list = load_live_team_options()

# --- Header Section ---
head_col1, head_col2 = st.columns([2.5, 2])

with head_col1:
    st.markdown("<h1 style='color: white; margin:0; font-weight: 700; font-size: 2rem;'>🏏 LiveStats Performance Overview</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; margin-top: 4px; margin-bottom: 20px;'>International & Domestic Cricket Analytics Portal</p>", unsafe_allow_html=True)

with head_col2:
    f1, f2, f3 = st.columns(3)
    format_filter = f1.selectbox("Format", ["All", "ODI", "T20I", "Test", "T20"])
    team_filter = f2.selectbox("Team", live_teams_list)
    year_filter = f3.selectbox("Season", ["All", "2026", "2025", "2024", "2023"])

# --- Key Metrics Row ---
try:
    total_players = pd.read_sql_query("SELECT COUNT(*) as cnt FROM players", conn)["cnt"][0]
    total_matches = pd.read_sql_query("SELECT COUNT(*) as cnt FROM matches", conn)["cnt"][0]
    total_teams = pd.read_sql_query("SELECT COUNT(*) as cnt FROM teams", conn)["cnt"][0]
    total_venues = pd.read_sql_query("SELECT COUNT(*) as cnt FROM venues", conn)["cnt"][0]
except Exception:
    total_players, total_matches, total_teams, total_venues = "--", "--", "--", "--"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="dashboard-card"><div class="kpi-title">Total Players</div><div class="kpi-value-cyan">{total_players}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="dashboard-card"><div class="kpi-title">Total Matches</div><div class="kpi-value-green">{total_matches}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="dashboard-card"><div class="kpi-title">Teams Tracked</div><div class="kpi-value-cyan">{total_teams}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="dashboard-card"><div class="kpi-title">Global Venues</div><div class="kpi-value-green">{total_venues}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SQL Analytics Hub Container ---
st.subheader("🔍 Select Business Intelligence Module")

# Difficulty Level Filter
level_filter = st.radio(
    "Filter by Question Level:",
    ["All Levels", "Beginner", "Intermediate", "Advanced"],
    horizontal=True
)

# ------------------------------------------------------------
# DYNAMIC FILTER BUILDER FUNCTION
# ------------------------------------------------------------
def apply_global_filters(base_sql, selected_format, selected_team, selected_year):
    """
    Appends SQL conditions and parameter values dynamically based on selected top filters.
    """
    conditions = []
    params = []

    if selected_format != "All":
        conditions.append("m.format = ?")
        params.append(selected_format)

    if selected_team != "All":
        conditions.append("(LOWER(t.team_name) = LOWER(?) OR LOWER(t1.team_name) = LOWER(?) OR LOWER(t2.team_name) = LOWER(?))")
        params.extend([selected_team, selected_team, selected_team])

    if selected_year != "All":
        conditions.append("(bp.year = ? OR strftime('%Y', m.match_date) = ?)")
        params.extend([int(selected_year), str(selected_year)])

    if not conditions:
        return base_sql, []

    filter_sql = " AND ".join(conditions)

    # Insert parameters into existing WHERE or start a new WHERE block
    if "WHERE" in base_sql.upper():
        formatted_sql = base_sql.replace("WHERE 1=1", f"WHERE 1=1 AND {filter_sql}")
        if "WHERE 1=1" not in base_sql:
            # Replace first instance of WHERE
            formatted_sql = base_sql.replace("WHERE", f"WHERE {filter_sql} AND ", 1)
    else:
        # Append WHERE condition before GROUP BY / ORDER BY / LIMIT
        if "GROUP BY" in base_sql.upper():
            parts = base_sql.split("GROUP BY", 1)
            formatted_sql = f"{parts[0]} WHERE {filter_sql} GROUP BY {parts[1]}"
        elif "ORDER BY" in base_sql.upper():
            parts = base_sql.split("ORDER BY", 1)
            formatted_sql = f"{parts[0]} WHERE {filter_sql} ORDER BY {parts[1]}"
        elif "LIMIT" in base_sql.upper():
            parts = base_sql.split("LIMIT", 1)
            formatted_sql = f"{parts[0]} WHERE {filter_sql} LIMIT {parts[1]}"
        else:
            formatted_sql = f"{base_sql} WHERE {filter_sql}"

    return formatted_sql, params

# ------------------------------------------------------------
# 25 BASE SQL QUESTIONS
# ------------------------------------------------------------
query_dict = {
    # --- BEGINNER (1-8) ---
    "Q1: All Players Representing Teams": {
        "level": "Beginner",
        "sql": """
            SELECT DISTINCT p.player_name AS "Player Name", COALESCE(t.team_name, 'N/A') AS "Team", p.role AS "Role"
            FROM players p 
            LEFT JOIN teams t ON p.team_id = t.team_id
            LEFT JOIN batting_performances bp ON p.player_id = bp.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            WHERE 1=1
            ORDER BY p.player_name;
        """
    },
    "Q2: Match Schedule Overview": {
        "level": "Beginner",
        "sql": """
            SELECT m.match_id AS "Match ID", m.series_name AS "Series", m.match_description AS "Match Description", 
                   t1.team_name AS "Team 1", t2.team_name AS "Team 2", m.format AS "Format", m.match_date AS "Date"
            FROM matches m
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
            WHERE 1=1
            LIMIT 20;
        """
    },
    "Q3: Top Run Scorers": {
        "level": "Beginner",
        "sql": """
            SELECT p.player_name AS "Player Name", SUM(bp.runs_scored) AS "Total Runs"
            FROM batting_performances bp
            JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Total Runs" DESC 
            LIMIT 10;
        """
    },
    "Q4: Stadiums and Capacity": {
        "level": "Beginner",
        "sql": """
            SELECT venue_name AS "Venue Name", city AS "City", country AS "Country", capacity AS "Capacity"
            FROM venues
            ORDER BY capacity DESC
            LIMIT 15;
        """
    },
    "Q5: Victories Count by Team": {
        "level": "Beginner",
        "sql": """
            SELECT t.team_name AS "Team Name", COUNT(m.match_id) AS "Total Victories"
            FROM matches m
            JOIN teams t ON m.winner_team_id = t.team_id
            WHERE 1=1
            GROUP BY t.team_id, t.team_name
            ORDER BY "Total Victories" DESC;
        """
    },
    "Q6: Player Distribution by Role": {
        "level": "Beginner",
        "sql": """
            SELECT p.role AS "Role", COUNT(*) AS "Total Players"
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.role
            ORDER BY "Total Players" DESC;
        """
    },
    "Q7: Highest Scores Recorded in an Innings": {
        "level": "Beginner",
        "sql": """
            SELECT p.player_name AS "Player Name", MAX(bp.runs_scored) AS "Highest Score", bp.balls_faced AS "Balls Faced"
            FROM batting_performances bp
            JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Highest Score" DESC
            LIMIT 15;
        """
    },
    "Q8: Tournament & Series Overview": {
        "level": "Beginner",
        "sql": """
            SELECT m.series_name AS "Series Name", COUNT(m.match_id) AS "Total Matches Scheduled"
            FROM matches m
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
            WHERE m.series_name IS NOT NULL AND m.series_name != ''
            GROUP BY m.series_name
            ORDER BY "Total Matches Scheduled" DESC
            LIMIT 15;
        """
    },

    # --- INTERMEDIATE (9-16) ---
    "Q9: Player Overall Performance Summary": {
        "level": "Intermediate",
        "sql": """
            SELECT 
                p.player_name AS "Player Name", 
                COALESCE(SUM(bp.runs_scored), 0) AS "Total Runs",
                COALESCE(SUM(bw.wickets_taken), 0) AS "Total Wickets"
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            LEFT JOIN batting_performances bp ON p.player_id = bp.player_id
            LEFT JOIN bowling_performances bw ON p.player_id = bw.player_id
            LEFT JOIN matches m ON (bp.match_id = m.match_id OR bw.match_id = m.match_id)
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Total Runs" DESC
            LIMIT 15;
        """
    },
    "Q10: Recent Completed Matches Detail": {
        "level": "Intermediate",
        "sql": """
            SELECT 
                m.match_description AS "Match Description", 
                w.team_name AS "Winner Team",
                m.margin AS "Margin",
                m.margin_type AS "Margin Type",
                m.format AS "Format"
            FROM matches m
            JOIN teams w ON m.winner_team_id = w.team_id
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
            WHERE 1=1
            LIMIT 15;
        """
    },
    "Q11: Batting Performance Analysis": {
        "level": "Intermediate",
        "sql": """
            SELECT 
                p.player_name AS "Player Name",
                COUNT(bp.match_id) AS "Innings Played",
                SUM(bp.runs_scored) AS "Total Runs",
                ROUND(AVG(bp.runs_scored), 2) AS "Average Runs",
                MAX(bp.runs_scored) AS "Highest Score"
            FROM players p
            JOIN batting_performances bp ON p.player_id = bp.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Total Runs" DESC
            LIMIT 15;
        """
    },
    "Q12: Teams Match Participation Count": {
        "level": "Intermediate",
        "sql": """
            SELECT 
                t.team_name AS "Team Name",
                COUNT(m.match_id) AS "Total Matches Played"
            FROM teams t
            LEFT JOIN matches m ON (t.team_id = m.team1_id OR t.team_id = m.team2_id)
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE 1=1
            GROUP BY t.team_id, t.team_name
            ORDER BY "Total Matches Played" DESC;
        """
    },
    "Q13: Toss Decisions & Win Impact": {
        "level": "Intermediate",
        "sql": """
            SELECT 
                m.toss_decision AS "Toss Decision",
                COUNT(m.match_id) AS "Total Times Chosen",
                SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS "Converted To Match Win"
            FROM matches m
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
            WHERE m.toss_decision IS NOT NULL AND m.toss_decision != ''
            GROUP BY m.toss_decision;
        """
    },
    "Q14: Team Match Performance": {
        "level": "Intermediate",
        "sql": """
            SELECT
                t.team_name AS "Team Name",
                COUNT(m.match_id) AS "Matches Played",
                SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS "Matches Won"
            FROM teams t
            LEFT JOIN matches m ON (t.team_id = m.team1_id OR t.team_id = m.team2_id)
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE 1=1
            GROUP BY t.team_id, t.team_name
            ORDER BY "Matches Won" DESC, "Matches Played" DESC
            LIMIT 15;
        """
    },
    "Q15: Boundary Hitters (Fours & Sixes)": {
        "level": "Intermediate",
        "sql": """
            SELECT p.player_name AS "Player Name", 
                   SUM(bp.fours) AS "Total Fours",
                   SUM(bp.sixes) AS "Total Sixes",
                   SUM(bp.fours * 4 + bp.sixes * 6) AS "Runs from Boundaries"
            FROM batting_performances bp
            JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Runs from Boundaries" DESC
            LIMIT 15;
        """
    },
    "Q16: Year-wise Batting Trend": {
        "level": "Intermediate",
        "sql": """
            SELECT bp.year AS "Year",
                   COUNT(DISTINCT bp.player_id) AS "Active Players",
                   SUM(bp.runs_scored) AS "Total Runs Scored",
                   ROUND(AVG(bp.runs_scored), 2) AS "Avg Runs per Innings"
            FROM batting_performances bp
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE bp.year IS NOT NULL
            GROUP BY bp.year
            ORDER BY bp.year DESC;
        """
    },

    # --- ADVANCED (17-25) ---
    "Q17: Team Win Rate Overview": {
        "level": "Advanced",
        "sql": """
            SELECT 
                t.team_name AS "Team Name",
                COUNT(m.match_id) AS "Total Matches",
                SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS "Total Wins",
                ROUND((SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1.0 ELSE 0 END) / NULLIF(COUNT(m.match_id), 0)) * 100, 2) AS "Win Rate (%)"
            FROM teams t
            LEFT JOIN matches m ON (t.team_id = m.team1_id OR t.team_id = m.team2_id)
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE 1=1
            GROUP BY t.team_id, t.team_name
            ORDER BY "Win Rate (%)" DESC;
        """
    },
    "Q18: Match Results by Winning Team": {
        "level": "Advanced",
        "sql": """
            SELECT
                t.team_name AS "Winning Team",
                COUNT(m.match_id) AS "Matches Won"
            FROM matches m
            JOIN teams t ON m.winner_team_id = t.team_id
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE m.winner_team_id IS NOT NULL
            GROUP BY t.team_id, t.team_name
            ORDER BY "Matches Won" DESC
            LIMIT 15;
        """
    },
    "Q19: Batting Consistency and Range Analysis": {
        "level": "Advanced",
        "sql": """
            SELECT p.player_name AS "Player Name", ROUND(AVG(bp.runs_scored), 2) AS "Avg Runs",
                   MIN(bp.runs_scored) AS "Min Score", MAX(bp.runs_scored) AS "Max Score"
            FROM batting_performances bp
            JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Avg Runs" DESC
            LIMIT 15;
        """
    },
    "Q20: Batting Position Impact Analysis": {
        "level": "Advanced",
        "sql": """
            SELECT bp.batting_position AS "Batting Position",
                   COUNT(*) AS "Innings Played",
                   SUM(bp.runs_scored) AS "Total Runs Scored",
                   ROUND(AVG(bp.runs_scored), 2) AS "Average Runs"
            FROM batting_performances bp
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE bp.batting_position IS NOT NULL
            GROUP BY bp.batting_position
            ORDER BY bp.batting_position ASC;
        """
    },
    "Q21: Player All-Rounder Ranking": {
        "level": "Advanced",
        "sql": """
            SELECT 
                p.player_name AS "Player Name",
                COALESCE(SUM(bp.runs_scored), 0) AS "Total Runs",
                COALESCE(SUM(bw.wickets_taken), 0) AS "Total Wickets",
                ROUND((COALESCE(SUM(bp.runs_scored), 0) * 0.1) + (COALESCE(SUM(bw.wickets_taken), 0) * 15), 2) AS "All-Rounder Rating"
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            LEFT JOIN batting_performances bp ON p.player_id = bp.player_id
            LEFT JOIN bowling_performances bw ON p.player_id = bw.player_id
            LEFT JOIN matches m ON (bp.match_id = m.match_id OR bw.match_id = m.match_id)
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "All-Rounder Rating" DESC
            LIMIT 15;
        """
    },
    "Q22: Head-to-Head Teams Match Summary": {
        "level": "Advanced",
        "sql": """
            SELECT 
                t1.team_name AS "Team 1", 
                t2.team_name AS "Team 2", 
                COUNT(*) AS "Total Head-to-Head Played"
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
            WHERE 1=1
            GROUP BY t1.team_name, t2.team_name
            ORDER BY "Total Head-to-Head Played" DESC
            LIMIT 15;
        """
    },
    "Q23: Player Form & Score Categorization": {
        "level": "Advanced",
        "sql": """
            SELECT p.player_name AS "Player Name", ROUND(AVG(bp.runs_scored), 2) AS "Average Runs",
                   SUM(CASE WHEN bp.runs_scored >= 50 THEN 1 ELSE 0 END) AS "50s Count",
                   CASE 
                     WHEN AVG(bp.runs_scored) >= 40 THEN 'High Impact'
                     WHEN AVG(bp.runs_scored) >= 20 THEN 'Consistent'
                     ELSE 'Developing'
                   END AS "Form Category"
            FROM batting_performances bp
            JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Average Runs" DESC
            LIMIT 15;
        """
    },
    "Q24: Dismissal Type Frequency Analysis": {
        "level": "Advanced",
        "sql": """
            SELECT bp.dismissal_status AS "Dismissal Type", COUNT(*) AS "Frequency"
            FROM batting_performances bp
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE bp.dismissal_status IS NOT NULL AND bp.dismissal_status != ''
            GROUP BY bp.dismissal_status
            ORDER BY "Frequency" DESC;
        """
    },
    "Q25: Career Performance Phase Classification": {
        "level": "Advanced",
        "sql": """
            SELECT p.player_name AS "Player Name",
                   ROUND(AVG(bp.runs_scored), 2) AS "Overall Avg",
                   CASE 
                     WHEN AVG(bp.runs_scored) > 35 THEN 'Ascending / Peak'
                     ELSE 'Stable / Support'
                   END AS "Career Phase"
            FROM batting_performances bp
            JOIN players p ON bp.player_id = p.player_id
            LEFT JOIN matches m ON bp.match_id = m.match_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE 1=1
            GROUP BY p.player_id, p.player_name
            ORDER BY "Overall Avg" DESC
            LIMIT 15;
        """
    }
}

# Filter question dropdown list by selected difficulty level
filtered_query_keys = [
    q_key for q_key, q_val in query_dict.items()
    if level_filter == "All Levels" or q_val["level"] == level_filter
]

selected_query_key = st.selectbox("Choose Analytical Question:", filtered_query_keys)
base_sql_query = query_dict[selected_query_key]["sql"].strip()

# Apply global dropdown filters dynamically to the base SQL statement
final_sql_query, sql_params = apply_global_filters(
    base_sql=base_sql_query, 
    selected_format=format_filter, 
    selected_team=team_filter, 
    selected_year=year_filter
)

with st.expander("📄 View Standardized SQL Execution Query", expanded=True):
    st.code(final_sql_query, language="sql")

# Query Execution
try:
    if conn is not None:
        df_result = pd.read_sql_query(final_sql_query, conn, params=sql_params)
        
        if df_result.empty:
            st.info("ℹ️ No matching records were found in the database for the selected filters.")
        else:
            st.dataframe(df_result, use_container_width=True)
            
            csv_data = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Result CSV",
                data=csv_data,
                file_name=f"{selected_query_key.split(':')[0]}_results.csv",
                mime="text/csv"
            )
    else:
        st.error("Database connection could not be established.")
except Exception as e:
    st.error(f"Error executing database query: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)