import sys
import importlib
import textwrap
from pathlib import Path
import streamlit as st

# Force project root directory into sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Reload modules
import utils.ui
import utils.api_client
importlib.reload(utils.ui)
importlib.reload(utils.api_client)

from utils.ui import apply_global_cricbuzz_theme, render_sidebar_header, render_sidebar_footer
from utils.api_client import get_live_matches

# Page Setup
st.set_page_config(
    page_title="Live Matches | Cricbuzz LiveStats",
    page_icon="🔴",
    layout="wide"
)

apply_global_cricbuzz_theme()

st.title("🔴 Live Match Scoreboard")
st.caption("Real-time match updates fetched directly from Cricbuzz API")

# Refresh Control
col_title, col_btn = st.columns([5, 1])
with col_btn:
    if st.button("🔄 Refresh Scores"):
        st.cache_data.clear()
        st.rerun()

# Fetch API Data
@st.cache_data(ttl=15)
def load_live_data():
    try:
        return get_live_matches()
    except Exception as e:
        st.error(f"Failed to fetch live matches: {e}")
        return None

raw_data = load_live_data()

# ============================================================
# PARSE AND RENDER SCORECARDS
# ============================================================

matches_found = False

if raw_data and "typeMatches" in raw_data:
    for match_type in raw_data.get("typeMatches", []):
        match_category = match_type.get("matchType", "Other Matches")
        
        for series in match_type.get("seriesMatches", []):
            series_wrapper = series.get("seriesAdWrapper", {})
            series_name = series_wrapper.get("seriesName", "Unknown Series")
            matches = series_wrapper.get("matches", [])

            for match in matches:
                matches_found = True
                info = match.get("matchInfo", {})
                score = match.get("matchScore", {})

                # Extract Team Details
                team1_name = info.get("team1", {}).get("teamName", "Team 1")
                team1_sname = info.get("team1", {}).get("teamSName", team1_name)
                
                team2_name = info.get("team2", {}).get("teamName", "Team 2")
                team2_sname = info.get("team2", {}).get("teamSName", team2_name)

                match_desc = info.get("matchDesc", "Match")
                match_format = info.get("matchFormat", "")
                status_str = info.get("status", "In Progress")
                state_str = info.get("state", "Live").capitalize()

                # Extract Live Scores
                t1_score_str = "Yet to Bat"
                t2_score_str = "Yet to Bat"

                if "team1Score" in score:
                    inngs = score["team1Score"].get("inngs1", {})
                    runs = inngs.get("runs", 0)
                    wkts = inngs.get("wickets", 0)
                    overs = inngs.get("overs", 0)
                    t1_score_str = f"{runs}/{wkts} ({overs} ov)"

                if "team2Score" in score:
                    inngs = score["team2Score"].get("inngs1", {})
                    runs = inngs.get("runs", 0)
                    wkts = inngs.get("wickets", 0)
                    overs = inngs.get("overs", 0)
                    t2_score_str = f"{runs}/{wkts} ({overs} ov)"

                # Determine badge color
                badge_bg = "#E53935" if state_str.lower() in ["live", "in progress"] else "#2E7D32"

                # Render Match Card HTML
                st.markdown(
                    textwrap.dedent(f"""
                    <div class="dashboard-card" style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2A2F35; padding-bottom: 8px; margin-bottom: 12px;">
                            <span style="color: #89939E; font-size: 0.8rem; font-weight: 600;">{series_name} • {match_desc} ({match_format})</span>
                            <span style="background-color: {badge_bg}; color: #FFFFFF; font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 4px;">{state_str.upper()}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0;">
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">{team1_name} ({team1_sname})</span>
                            </div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #00D2FF;">
                                {t1_score_str}
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0;">
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">{team2_name} ({team2_sname})</span>
                            </div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #00D2FF;">
                                {t2_score_str}
                            </div>
                        </div>
                        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #2A2F35; color: #00E676; font-size: 0.85rem; font-weight: 600;">
                            📣 {status_str}
                        </div>
                    </div>
                    """),
                    unsafe_allow_html=True
                )

if not matches_found:
    st.info("No live or recent matches found in the API feed at the moment.")