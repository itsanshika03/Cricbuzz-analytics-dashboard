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
importlib.reload(utils.ui)
importlib.reload(utils.db_connection)
importlib.reload(utils.api_client)

from utils.ui import apply_global_cricbuzz_theme
from utils.db_connection import get_db_connection
from utils.api_client import get_live_team_names
from utils.api_client import get_live_team_names, get_players_by_team_name

st.set_page_config(
    page_title="CRUD Operations | LiveStats",
    page_icon="🛠️",
    layout="wide"
)

apply_global_cricbuzz_theme()

st.title("🛠️ Player Database CRUD Operations")
st.caption("Manage player records stored in the local SQLite database using CRUD operations.")

conn = get_db_connection()

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicketkeeper-Batsman"]
BATTING_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWLING_STYLES = [
    "None", "Right-arm fast", "Right-arm medium", "Right-arm offbreak", 
    "Right-arm legbreak", "Left-arm fast", "Left-arm orthodox", "Left-arm chinaman"
]

# ============================================================
# TAB SELECTION
# ============================================================

tab_read, tab_create, tab_update, tab_delete = st.tabs([
    "📋 Read Players", 
    "➕ Add New Player", 
    "✏️ Update Record", 
    "🗑️ Delete Record"
])

# ------------------------------------------------------------
# 1. READ PLAYERS
# ------------------------------------------------------------
with tab_read:
    st.subheader("Current Database Records")
    
    if conn:
        query = """
        SELECT 
            p.player_id AS "Player ID",
            p.player_name AS "Player Name",
            COALESCE(t.team_name, 'N/A') AS "Team",
            COALESCE(p.role, 'N/A') AS "Role",
            COALESCE(p.batting_style, 'N/A') AS "Batting Style",
            COALESCE(p.bowling_style, 'N/A') AS "Bowling Style"
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.team_id
        ORDER BY p.player_id ASC;
    """
    df_players = pd.read_sql_query(query, conn)
    st.dataframe(df_players, use_container_width=True)

# ------------------------------------------------------------
# 2. CREATE PLAYER TAB
# ------------------------------------------------------------
with tab_create:
    st.subheader("Add New Player Entry")
    
    if conn:
        # Load teams from local database
        teams_df = pd.read_sql_query("SELECT team_id, team_name FROM teams", conn)
        team_dict = dict(zip(teams_df["team_name"], teams_df["team_id"])) if not teams_df.empty else {}

        # Combine active live teams with database teams
        live_teams = get_live_team_names() or []
        combined_teams = sorted(list(set([t for t in live_teams + list(team_dict.keys()) if t])))

        st.markdown("### ⚡ Team Roster & Auto-Fill")
        st.caption("Select a team below to load its players into the dropdown.")

        c1, c2 = st.columns(2)
        with c1:
            selected_team = st.selectbox(
                "1. Choose Team", 
                ["-- Select Team --"] + combined_teams,
                key="team_selector_main"
            )

        # Dynamic fetching on selection
        fetched_players = []
        if selected_team and selected_team != "-- Select Team --":
            with st.spinner(f"Fetching squad roster for {selected_team}..."):
                fetched_players = get_players_by_team_name(selected_team, db_conn=conn)

        with c2:
            if selected_team == "-- Select Team --":
                st.selectbox("2. Select Player from Squad Dropdown", ["Select a team first"], disabled=True, key="p_dis")
                selected_player = None
            elif fetched_players:
                selected_player = st.selectbox("2. Select Player from Squad Dropdown", ["-- Type Manually --"] + fetched_players, key="p_active")
            else:
                st.selectbox("2. Select Player from Squad Dropdown", ["No live squad found (Type manually below)"], disabled=True, key="p_none")
                selected_player = None

        st.divider()

        # Handle form field values
        autofill_name = ""
        if selected_player and selected_player != "-- Type Manually --":
            autofill_name = selected_player

        db_teams = list(team_dict.keys())
        if selected_team and selected_team != "-- Select Team --" and selected_team not in db_teams:
            db_teams.insert(0, selected_team)

        default_team_idx = 0
        if selected_team and selected_team in db_teams:
            default_team_idx = db_teams.index(selected_team)

        # ENTRY FORM
        with st.form("create_player_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Player Name *", value=autofill_name, placeholder="e.g. Jasprit Bumrah")
                new_role = st.selectbox("Role *", ["Batsman", "Bowler", "All-Rounder", "WK-Batsman"])
                
                selected_team_name = st.selectbox("Assign Database Team *", db_teams if db_teams else ["Default Team"], index=default_team_idx)
                
            with col2:
                new_batting = st.selectbox("Batting Style *", ["Right-hand bat", "Left-hand bat", "Right-handed"])
                new_bowling = st.selectbox("Bowling Style *", ["None", "Right-arm fast", "Right-arm medium", "Right-arm spin", "Left-arm fast", "Left-arm spin"])

            submit_create = st.form_submit_button("➕ Save Player to Database")

            if submit_create:
                if not new_name.strip():
                    st.error("Please enter a valid player name.")
                else:
                    try:
                        cursor = conn.cursor()

                        # Auto-create missing team in local DB if needed
                        if selected_team_name not in team_dict:
                            cursor.execute("INSERT INTO teams (team_name) VALUES (?)", (selected_team_name,))
                            conn.commit()
                            final_team_id = cursor.lastrowid
                        else:
                            final_team_id = team_dict[selected_team_name]

                        # Insert player into database
                        cursor.execute("""
                            INSERT INTO players (player_name, team_id, role, batting_style, bowling_style)
                            VALUES (?, ?, ?, ?, ?)
                        """, (new_name.strip(), final_team_id, new_role, new_batting, new_bowling))
                        
                        conn.commit()
                        st.success(f"Successfully added **{new_name}** under **{selected_team_name}**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create record: {e}")

# ------------------------------------------------------------
# 3. UPDATE PLAYER
# ------------------------------------------------------------
with tab_update:
    st.subheader("Modify Existing Player Record")
    
    if conn:
        players_list_df = pd.read_sql_query("SELECT player_id, player_name FROM players", conn)
        
        if players_list_df.empty:
            st.info("No players available to update.")
        else:
            player_map = dict(zip(players_list_df["player_name"], players_list_df["player_id"]))
            selected_player_name = st.selectbox("Select Player to Edit:", list(player_map.keys()))
            selected_player_id = player_map[selected_player_name]
            
            current_data = pd.read_sql_query(
                "SELECT * FROM players WHERE player_id = ?", conn, params=(selected_player_id,)
            ).iloc[0]

            with st.form("update_player_form"):
                col1, col2 = st.columns(2)
                with col1:
                    updated_name = st.text_input("Player Name", value=current_data["player_name"])
                    role_idx = ROLES.index(current_data["role"]) if current_data["role"] in ROLES else 0
                    updated_role = st.selectbox("Role", ROLES, index=role_idx)
                    
                with col2:
                    bat_idx = BATTING_STYLES.index(current_data["batting_style"]) if current_data["batting_style"] in BATTING_STYLES else 0
                    updated_batting = st.selectbox("Batting Style", BATTING_STYLES, index=bat_idx)
                    
                    bowl_idx = BOWLING_STYLES.index(current_data["bowling_style"]) if current_data["bowling_style"] in BOWLING_STYLES else 0
                    updated_bowling = st.selectbox("Bowling Style", BOWLING_STYLES, index=bowl_idx)

                submit_update = st.form_submit_button("✏️ Apply Changes")

                if submit_update:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE players 
                            SET player_name = ?, role = ?, batting_style = ?, bowling_style = ?
                            WHERE player_id = ?
                        """, (updated_name, updated_role, updated_batting, updated_bowling, selected_player_id))
                        conn.commit()
                        st.success(f"Record for **{updated_name}** updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating record: {e}")

# ------------------------------------------------------------
# 4. DELETE PLAYER
# ------------------------------------------------------------
with tab_delete:
    st.subheader("Delete Player Entry")
    
    if conn:
        players_del_df = pd.read_sql_query("SELECT player_id, player_name FROM players", conn)
        
        if players_del_df.empty:
            st.info("No records to delete.")
        else:
            del_map = dict(zip(players_del_df["player_name"], players_del_df["player_id"]))
            target_name = st.selectbox("Select Player to Delete:", list(del_map.keys()))
            target_id = del_map[target_name]
            
            st.warning(f"⚠️ Are you sure you want to delete **{target_name}** (ID: {target_id})? This operation cannot be undone.")
            
            if st.button("🗑️ Confirm Delete Record", type="primary"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM players WHERE player_id = ?", (target_id,))
                    conn.commit()
                    st.success(f"Record for **{target_name}** deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete record: {e}")