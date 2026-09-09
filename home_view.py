import streamlit as st
import pandas as pd

from utils.ui import apply_global_cricbuzz_theme
from utils.db_connection import get_db_connection

from utils.api_client import (
    get_live_match_list,
    get_live_matches_with_meta
)


def render_overview_page():

    # Apply theme
    apply_global_cricbuzz_theme()

    # ============================================================
    # PAGE HEADER
    # ============================================================

    st.title("Cricbuzz Analytics Overview")

    st.caption(
        "Real-time cricket scores, player statistics, and interactive intelligence hub."
    )

    # ============================================================
    # LIVE MATCH CENTER
    # ============================================================

    st.subheader("🔴 Live Match Center")

    @st.fragment(run_every=30)
    def render_live_match_ticker():

        try:
            live_matches = get_live_match_list()

        except Exception as e:
            live_matches = []
            st.error(f"Unable to fetch live Cricbuzz data: {e}")

        # --------------------------------------------------------
        # LIVE MATCHES
        # --------------------------------------------------------

        if live_matches:

            display_matches = live_matches[:3]

            ticker_cols = st.columns(len(display_matches))

            for idx, match in enumerate(display_matches):

                with ticker_cols[idx]:

                    team1 = match.get("team1", "Team 1")
                    team2 = match.get("team2", "Team 2")

                    series_name = match.get(
                        "series",
                        "Live Cricket"
                    )

                    status = match.get("status", "")
                    state = match.get("state", "")

                    description = match.get(
                        "description",
                        "Live Match"
                    )

                    venue = match.get("venue", "")
                    city = match.get("city", "")

                    format_name = match.get(
                        "format",
                        ""
                    )

                    # Venue
                    if venue and city:
                        venue_text = f"{venue}, {city}"
                    elif venue:
                        venue_text = venue
                    elif city:
                        venue_text = city
                    else:
                        venue_text = "Venue unavailable"

                    # Status
                    if status:
                        status_text = status
                    elif state:
                        status_text = state
                    else:
                        status_text = "Live"

                    # Use Streamlit native container
                    with st.container(border=True):

                        st.caption(series_name)

                        st.markdown(
                            f"### {team1} vs {team2}"
                        )

                        st.success(
                            f"🔴 {status_text}"
                        )

                        st.write(description)

                        if format_name:
                            format_display = format_name.upper()
                        else:
                            format_display = "CRICKET"

                        st.caption(
                            f"{format_display} • {venue_text}"
                        )

        # --------------------------------------------------------
        # NO LIVE MATCHES
        # --------------------------------------------------------

        else:

            st.info(
                "No live matches right now. "
                "Cricbuzz API will automatically update when a live match becomes available."
            )

    render_live_match_ticker()

    # ============================================================
    # DATABASE METRICS
    # ============================================================

    try:

        conn = get_db_connection()

        # --------------------------------------------------------
        # ACTIVE SERIES
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # TOTAL BALLS
        # --------------------------------------------------------

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
            formatted_balls = f"{total_balls / 1000:.1f}k"
        else:
            formatted_balls = str(total_balls)

        # --------------------------------------------------------
        # TOP PERFORMER
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # SQL QUESTIONS
        # --------------------------------------------------------

        sql_question_count = 25

        conn.close()

    except Exception:

        series_count = 0
        formatted_balls = "0"
        top_player = "N/A"
        top_stats = "No records"
        sql_question_count = 0

    # ============================================================
    # KEY PLATFORM METRICS
    # ============================================================

    st.subheader("⚡ Key Platform Metrics")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # KPI 1
    with kpi1:

        st.metric(
            label="Active Series Tracked",
            value=f"{series_count} Series"
        )

        st.caption(
            "SQLite analytical dataset"
        )

    # KPI 2
    with kpi2:

        st.metric(
            label="Total Deliveries Indexed",
            value=formatted_balls
        )

        st.caption(
            "SQLite batting records"
        )

    # KPI 3
    with kpi3:

        st.metric(
            label="Top Record Holder",
            value=top_player
        )

        st.caption(
            top_stats
        )

    # KPI 4
    with kpi4:

        st.metric(
            label="Analytical Queries",
            value=f"{sql_question_count} SQL"
        )

        st.caption(
            "Pre-built templates"
        )

    # ============================================================
    # SEARCH + SYSTEM STATUS
    # ============================================================

    left_col, right_col = st.columns(
        [1.8, 1.2],
        gap="large"
    )

    # ============================================================
    # PLAYER SEARCH
    # ============================================================

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

    # ============================================================
    # LIVE SYSTEM STATUS
    # ============================================================

    with right_col:

        st.subheader(
            "⚡ Live System Status"
        )

        # --------------------------------------------------------
        # API STATUS
        # --------------------------------------------------------

        try:

            _, api_latency, api_error = (
                get_live_matches_with_meta()
            )

            if api_error:

                api_status = "API Error"

            else:

                api_status = "Connected"

        except Exception:

            api_latency = 0
            api_error = "Unable to connect"
            api_status = "Unavailable"

        # --------------------------------------------------------
        # DATABASE STATUS
        # --------------------------------------------------------

        try:

            test_conn = get_db_connection()

            test_conn.execute(
                "SELECT 1"
            )

            test_conn.close()

            database_status = "Connected"

        except Exception:

            database_status = "Unavailable"

        # --------------------------------------------------------
        # DISPLAY STATUS
        # --------------------------------------------------------

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

if __name__ == "__main__":
    render_overview_page()