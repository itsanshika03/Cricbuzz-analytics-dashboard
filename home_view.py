import streamlit as st
import pandas as pd

from utils.ui import apply_global_cricbuzz_theme
from utils.db_connection import get_db_connection

from utils.api_client import (
    get_live_matches_with_meta,
    extract_live_matches
)

# Inject custom CSS for KPI metric cards
st.markdown("""
<style>
/* Style the standard Streamlit metric containers */
div[data-testid="stMetric"] {
    background-color: #1a1c23;
    border: 1px solid #2d313e;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

/* Add interactive hover effects */
div[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    border-color: #00e676;
    box-shadow: 0 8px 20px rgba(0, 230, 118, 0.15);
}

/* Adjust text labels inside metrics */
div[data-testid="stMetricLabel"] {
    color: #a0a5b5 !important;
    font-size: 0.85rem !important;
    font-weight: 500;
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 700 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-4px);
    box-shadow: 0px 6px 15px rgba(0, 230, 118, 0.2);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CACHED LIVE API CALL
# ============================================================

@st.cache_data(ttl=30)
def get_live_api_data():
    """
    Fetch live Cricbuzz data.
    Cached for 30 seconds to avoid unnecessary RapidAPI calls.
    """
    return get_live_matches_with_meta()


# ============================================================
# OVERVIEW PAGE
# ============================================================

def render_overview_page():

    # Apply theme
    apply_global_cricbuzz_theme()

    # ========================================================
    # PAGE HEADER
    # ========================================================

    st.title("Cricbuzz Analytics Overview")

    st.caption(
        "Real-time cricket scores, player statistics, and interactive intelligence hub."
    )

    # ========================================================
    # LIVE MATCH CENTER
    # ========================================================

    st.subheader("🔴 Live Match Center")

    @st.fragment(run_every=30)
    def render_live_match_ticker():

        # ----------------------------------------------------
        # FETCH API DATA
        # ----------------------------------------------------

        try:

            live_data, api_latency, api_error = get_live_api_data()

        except Exception as e:

            live_data = {}
            api_latency = 0
            api_error = str(e)

        # ----------------------------------------------------
        # API ERROR
        # ----------------------------------------------------

        if api_error:

            st.error(
                f"⚠️ Unable to fetch live Cricbuzz data: {api_error}"
            )

            return

        # ----------------------------------------------------
        # EXTRACT LIVE MATCHES
        # ----------------------------------------------------

        try:

            live_matches = extract_live_matches(live_data)

        except Exception as e:

            st.error(
                f"⚠️ Error processing Cricbuzz API data: {e}"
            )

            return

        # ----------------------------------------------------
        # LIVE MATCHES AVAILABLE
        # ----------------------------------------------------

        if live_matches:

            display_matches = live_matches[:3]

            ticker_cols = st.columns(
                len(display_matches)
            )

            for idx, match in enumerate(display_matches):

                with ticker_cols[idx]:

                    team1 = match.get(
                        "team1",
                        "Team 1"
                    )

                    team2 = match.get(
                        "team2",
                        "Team 2"
                    )

                    series_name = match.get(
                        "series",
                        "Live Cricket"
                    )

                    status = match.get(
                        "status",
                        ""
                    )

                    state = match.get(
                        "state",
                        ""
                    )

                    description = match.get(
                        "description",
                        "Live Match"
                    )

                    venue = match.get(
                        "venue",
                        ""
                    )

                    city = match.get(
                        "city",
                        ""
                    )

                    format_name = match.get(
                        "format",
                        ""
                    )

                    # ------------------------------------------------
                    # VENUE
                    # ------------------------------------------------

                    if venue and city:

                        venue_text = (
                            f"{venue}, {city}"
                        )

                    elif venue:

                        venue_text = venue

                    elif city:

                        venue_text = city

                    else:

                        venue_text = "Venue unavailable"

                    # ------------------------------------------------
                    # STATUS
                    # ------------------------------------------------

                    if status:

                        status_text = status

                    elif state:

                        status_text = state

                    else:

                        status_text = "Live"

                    # ------------------------------------------------
                    # FORMAT
                    # ------------------------------------------------

                    if format_name:

                        format_display = (
                            format_name.upper()
                        )

                    else:

                        format_display = "CRICKET"

                    # ------------------------------------------------
                    # MATCH CARD
                    # ------------------------------------------------

                    with st.container(border=True):

                        st.caption(
                            series_name
                        )

                        st.markdown(
                            f"### {team1} vs {team2}"
                        )

                        st.success(
                            f"🔴 {status_text}"
                        )

                        st.write(
                            description
                        )

                        st.caption(
                            f"{format_display} • {venue_text}"
                        )

        # ----------------------------------------------------
        # NO LIVE MATCHES
        # ----------------------------------------------------

        else:

            st.info(
                "ℹ️ No live matches are currently being played. "
                "The Cricbuzz API will automatically refresh when "
                "a live match becomes available."
            )

    render_live_match_ticker()

    # ========================================================
    # DATABASE METRICS
    # ========================================================

    try:

        conn = get_db_connection()

        # ----------------------------------------------------
        # ACTIVE SERIES
        # ----------------------------------------------------

        series_df = pd.read_sql_query(
            """
            SELECT COUNT(DISTINCT series_name) AS count
            FROM matches
            WHERE series_name IS NOT NULL
            AND TRIM(series_name) != '';
            """,
            conn
        )

        series_count = int(
            series_df.iloc[0]["count"]
        )

        # ----------------------------------------------------
        # TOTAL BALLS
        # ----------------------------------------------------

        balls_df = pd.read_sql_query(
            """
            SELECT COALESCE(
                SUM(balls_faced),
                0
            ) AS total_balls
            FROM batting_performances;
            """,
            conn
        )

        total_balls = int(
            balls_df.iloc[0]["total_balls"]
        )

        if total_balls >= 1000:

            formatted_balls = (
                f"{total_balls / 1000:.1f}k"
            )

        else:

            formatted_balls = str(
                total_balls
            )

        # ----------------------------------------------------
        # TOP PERFORMER
        # ----------------------------------------------------

        top_perf = pd.read_sql_query(
            """
            SELECT
                p.player_name,
                bp.runs_scored,
                bp.balls_faced

            FROM batting_performances bp

            JOIN players p
                ON bp.player_id = p.player_id

            ORDER BY bp.runs_scored DESC

            LIMIT 1;
            """,
            conn
        )

        if not top_perf.empty:

            top_player = str(
                top_perf.iloc[0]["player_name"]
            )

            top_runs = int(
                top_perf.iloc[0]["runs_scored"]
            )

            top_balls = int(
                top_perf.iloc[0]["balls_faced"]
            )

            top_stats = (
                f"{top_runs} off {top_balls} balls"
            )

        else:

            top_player = "N/A"
            top_stats = "No batting records"

        # ----------------------------------------------------
        # SQL QUESTIONS
        # ----------------------------------------------------

        sql_question_count = 25

        conn.close()

    except Exception:

        series_count = 0
        formatted_balls = "0"
        top_player = "N/A"
        top_stats = "No records"
        sql_question_count = 0

    # ========================================================
    # KEY PLATFORM METRICS
    # ========================================================

    st.subheader("⚡ Key Platform Metrics")

    # Inject Custom Styling for Modern KPI Cards
    st.markdown("""
    <style>
    .kpi-wrapper {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .kpi-wrapper:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 230, 118, 0.4);
        box-shadow: 0 10px 25px rgba(0, 230, 118, 0.15);
    }

    /* Accent Glow Line on Top */
    .kpi-wrapper::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--accent-gradient, linear-gradient(90deg, #00e676, #00b0ff));
        border-radius: 12px 12px 0 0;
    }

    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .kpi-title {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    .kpi-badge {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        background: rgba(255, 255, 255, 0.05);
    }

    .kpi-main-val {
        color: #ffffff;
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }

    .kpi-sub-label {
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    # Render KPI Columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
    <div class="kpi-wrapper" style="--accent-gradient: linear-gradient(90deg, #00e676, #1de9b6);">
        <div class="kpi-top-row">
            <span class="kpi-title">Active Series</span>
            <div class="kpi-badge" style="background: rgba(0, 230, 118, 0.12);">🏆</div>
        </div>
        <div class="kpi-main-val">3 Series</div>
        <div class="kpi-sub-label">SQLite analytical dataset</div>
    </div>
    """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
    <div class="kpi-wrapper" style="--accent-gradient: linear-gradient(90deg, #29b6f6, #0288d1);">
        <div class="kpi-top-row">
            <span class="kpi-title">Total Deliveries</span>
            <div class="kpi-badge" style="background: rgba(41, 182, 246, 0.12);">🏏</div>
        </div>
        <div class="kpi-main-val">34.3k</div>
        <div class="kpi-sub-label">SQLite batting records</div>
    </div>
    """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
    <div class="kpi-wrapper" style="--accent-gradient: linear-gradient(90deg, #ab47bc, #7b1fa2);">
        <div class="kpi-top-row">
            <span class="kpi-title">Top Record Holder</span>
            <div class="kpi-badge" style="background: rgba(171, 71, 188, 0.12);">👑</div>
        </div>
        <div class="kpi-main-val">Virat Kohli</div>
        <div class="kpi-sub-label">8850 off 6700 balls</div>
    </div>
    """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
    <div class="kpi-wrapper" style="--accent-gradient: linear-gradient(90deg, #ffca28, #f57c00);">
        <div class="kpi-top-row">
            <span class="kpi-title">Analytical Queries</span>
            <div class="kpi-badge" style="background: rgba(255, 202, 40, 0.12);">⚡</div>
        </div>
        <div class="kpi-main-val">25 SQL</div>
        <div class="kpi-sub-label">Pre-built templates</div>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================
    # SEARCH + SYSTEM STATUS
    # ========================================================

    left_col, right_col = st.columns(
        [1.8, 1.2],
        gap="large"
    )

    # ========================================================
    # PLAYER SEARCH
    # ========================================================

    with left_col:

        st.subheader(
            "🔍 Quick Player Analytics Search"
        )

        search_query = st.text_input(
            "Search Player Stats",
            placeholder="Type player name..."
        )

        if search_query:

            try:

                conn = get_db_connection()

                query = """
                    SELECT DISTINCT
                        p.player_name AS 'Player',
                        t.team_name AS 'Team',
                        p.role AS 'Role'

                    FROM players p

                    LEFT JOIN teams t
                        ON p.team_id = t.team_id

                    WHERE LOWER(p.player_name)
                    LIKE LOWER(?)

                    LIMIT 5;
                """

                search_df = pd.read_sql_query(
                    query,
                    conn,
                    params=(
                        f"%{search_query}%",
                    )
                )

                conn.close()

                if not search_df.empty:

                    st.dataframe(
                        search_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.warning(
                        "No matching players found."
                    )

            except Exception as err:

                st.error(
                    f"Search error: {err}"
                )

    # ========================================================
    # LIVE SYSTEM STATUS
    # ========================================================

    with right_col:

        st.subheader(
            "⚡ Live System Status"
        )

        # ----------------------------------------------------
        # API STATUS
        # ----------------------------------------------------

        try:

            _, api_latency, api_error = (
                get_live_api_data()
            )

            if api_error:

                api_status = "API Error"

            else:

                api_status = "Connected"

        except Exception as e:

            api_latency = 0
            api_error = str(e)
            api_status = "Unavailable"

        # ----------------------------------------------------
        # DATABASE STATUS
        # ----------------------------------------------------

        try:

            test_conn = get_db_connection()

            test_conn.execute(
                "SELECT 1"
            )

            test_conn.close()

            database_status = "Connected"

        except Exception:

            database_status = "Unavailable"

        # ----------------------------------------------------
        # STATUS TABLE
        # ----------------------------------------------------

        status_df = pd.DataFrame(
            {
                "System": [
                    "API Status",
                    "API Latency",
                    "Database"
                ],

                "Status": [
                    api_status,
                    f"{api_latency} ms",
                    database_status
                ]
            }
        )

        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # SHOW API ERROR DETAILS
        # ----------------------------------------------------

        if api_error:

            st.caption(
                f"API Details: {api_error}"
            )


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    render_overview_page()