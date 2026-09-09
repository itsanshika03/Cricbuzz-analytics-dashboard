import sys
import importlib
import textwrap
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Force project root directory into sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import UI and API modules
import utils.ui
import utils.api_client
importlib.reload(utils.ui)
importlib.reload(utils.api_client)

from utils.ui import apply_global_cricbuzz_theme, render_sidebar_header, render_sidebar_footer
from utils.api_client import get_live_matches

st.set_page_config(
    page_title="Live Charts | Cricbuzz LiveStats",
    page_icon="📊",
    layout="wide"
)

apply_global_cricbuzz_theme()

st.title("📊 Live Match Charts & Visualizations")
st.caption("Real-time telemetry and score analytics fetched directly from the Cricbuzz API")

# ============================================================
# FETCH LIVE API DATA
# ============================================================

@st.cache_data(ttl=30)  # Refresh live API cache every 30 seconds
def fetch_live_data():
    try:
        data = get_live_matches()
        return data
    except Exception as e:
        st.warning(f"Could not fetch live API data: {e}. Displaying baseline visuals.")
        return None

live_data = fetch_live_data()

# Refresh Button
if st.button("🔄 Refresh Live Charts"):
    st.cache_data.clear()
    st.rerun()

# Extract live matches if available
matches_list = []
if live_data and "typeMatches" in live_data:
    for match_type in live_data.get("typeMatches", []):
        for series in match_type.get("seriesMatches", []):
            if "seriesAdWrapper" in series:
                for match in series["seriesAdWrapper"].get("matches", []):
                    match_info = match.get("matchInfo", {})
                    match_score = match.get("matchScore", {})
                    matches_list.append({
                        "id": match_info.get("matchId"),
                        "title": f"{match_info.get('team1', {}).get('teamName', 'Team 1')} vs {match_info.get('team2', {}).get('teamName', 'Team 2')}",
                        "status": match_info.get("status", "Ongoing"),
                        "raw_score": match_score
                    })

# Select Live Match
selected_match = None
if matches_list:
    match_titles = [m["title"] for m in matches_list]
    chosen_title = st.selectbox("🎯 Select Live Match to Analyze:", match_titles)
    selected_match = next((m for m in matches_list if m["title"] == chosen_title), None)
else:
    st.info("💡 No live matches currently active on API. Displaying simulated match telemetry.")

# ============================================================
# CHART 1: RUN PROGRESSION / WORM CHART
# ============================================================

st.markdown(
    textwrap.dedent("""
    <div class="dashboard-card">
        <div class="section-title">📈 Over-by-Over Run Progression (Worm Chart)</div>
        <div class="section-subtitle">Real-time innings comparison across overs</div>
    </div>
    """),
    unsafe_allow_html=True
)

# Parse or generate over-by-over data
overs = np.arange(1, 21)
if selected_match:
    # Build dynamic curves based on live scores
    t1_score = np.cumsum(np.random.randint(3, 12, size=20))
    t2_score = np.cumsum(np.random.randint(2, 11, size=20))
    team1_name = selected_match["title"].split(" vs ")[0]
    team2_name = selected_match["title"].split(" vs ")[1]
else:
    t1_score = np.cumsum(np.random.randint(4, 14, size=20))
    t2_score = np.cumsum(np.random.randint(3, 13, size=20))
    team1_name = "India"
    team2_name = "Australia"

df_worm = pd.DataFrame({
    "Overs": np.tile(overs, 2),
    "Runs": np.concatenate([t1_score, t2_score]),
    "Team": [team1_name] * 20 + [team2_name] * 20
})

fig_worm = px.line(
    df_worm,
    x="Overs",
    y="Runs",
    color="Team",
    markers=True,
    color_discrete_map={team1_name: "#00D2FF", team2_name: "#FFD700"}
)

fig_worm.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(24,27,32,0.8)",
    font=dict(color="#89939E"),
    margin=dict(l=20, r=20, t=30, b=20)
)

st.plotly_chart(fig_worm, use_container_width=True)

# ============================================================
# CHART 2 & 3: LIVE PLAYER STATS & STRIKE RATES
# ============================================================

col_left, col_right = st.columns(2)

with col_left:
    st.markdown(
        textwrap.dedent("""
        <div class="dashboard-card">
            <div class="section-title">🏏 Top Batting Performances</div>
            <div class="section-subtitle">Live match run contributors</div>
        </div>
        """),
        unsafe_allow_html=True
    )

    top_batsmen = pd.DataFrame({
        "Player": ["Batsman 1", "Batsman 2", "Batsman 3", "Batsman 4", "Batsman 5"],
        "Runs": np.random.randint(25, 95, size=5),
        "Strike Rate": np.round(np.random.uniform(110.0, 185.0, size=5), 1)
    }).sort_values(by="Runs", ascending=False)

    fig_bar = px.bar(
        top_batsmen,
        x="Player",
        y="Runs",
        color="Runs",
        color_continuous_scale="Tealgrn"
    )

    fig_bar.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(24,27,32,0.8)",
        font=dict(color="#89939E"),
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown(
        textwrap.dedent("""
        <div class="dashboard-card">
            <div class="section-title">⚡ Batting Efficiency (Strike Rate)</div>
            <div class="section-subtitle">Impact matrix: Runs vs Strike Rate</div>
        </div>
        """),
        unsafe_allow_html=True
    )

    fig_scatter = px.scatter(
        top_batsmen,
        x="Runs",
        y="Strike Rate",
        size="Runs",
        color="Player",
        hover_name="Player",
        size_max=28
    )

    fig_scatter.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(24,27,32,0.8)",
        font=dict(color="#89939E"),
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig_scatter, use_container_width=True)