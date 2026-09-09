import time
import requests
import streamlit as st


# ============================================================
# CRICBUZZ RAPIDAPI CONFIGURATION
# ============================================================

API_BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"


# ============================================================
# API HEADERS
# ============================================================

def get_cricbuzz_headers():
    """Retrieve RapidAPI credentials securely from Streamlit secrets."""

    api_key = st.secrets.get("CRICBUZZ_API_KEY", "")
    api_host = st.secrets.get(
        "CRICBUZZ_API_HOST",
        "cricbuzz-cricket.p.rapidapi.com"
    )

    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host
    }


# ============================================================
# GENERIC API REQUEST
# ============================================================

def _get_json(endpoint, params=None, timeout=10):
    """
    Make a GET request to Cricbuzz RapidAPI.

    Returns:
        data, latency_ms, error
    """

    headers = get_cricbuzz_headers()

    if not headers.get("x-rapidapi-key"):
        return {}, 0, "CRICBUZZ_API_KEY is missing from Streamlit secrets."

    start_time = time.perf_counter()

    try:

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=headers,
            params=params,
            timeout=timeout
        )

        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        if response.status_code == 200:

            return response.json(), latency_ms, None

        return (
            {},
            latency_ms,
            f"API returned HTTP {response.status_code}"
        )

    except requests.RequestException as e:

        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        return {}, latency_ms, str(e)


# ============================================================
# LIVE MATCHES
# ============================================================

@st.cache_data(ttl=30)
def get_live_matches():
    """
    Fetch currently live matches from Cricbuzz RapidAPI.
    """

    data, _, _ = _get_json(
        "/matches/v1/live"
    )

    return data


def get_live_matches_with_meta():
    """
    Fetch live matches along with API latency and error information.

    Returns:
        data, latency_ms, error
    """

    return _get_json(
        "/matches/v1/live"
    )


# ============================================================
# EXTRACT / FLATTEN LIVE MATCHES
# ============================================================

def extract_live_matches(data):
    """
    Convert Cricbuzz's nested live-match response
    into a simple list of match dictionaries.
    """

    matches = []

    if not data:
        return matches

    type_matches = data.get(
        "typeMatches",
        []
    )

    for match_type in type_matches:

        match_type_name = match_type.get(
            "matchType",
            ""
        )

        series_matches = match_type.get(
            "seriesMatches",
            []
        )

        for series in series_matches:

            wrapper = series.get(
                "seriesAdWrapper",
                {}
            )

            if not isinstance(wrapper, dict):
                continue

            series_name = wrapper.get(
                "seriesName",
                "Live Cricket"
            )

            series_id = wrapper.get(
                "seriesId"
            )

            for match in wrapper.get(
                "matches",
                []
            ):

                info = match.get(
                    "matchInfo",
                    {}
                )

                if not isinstance(info, dict):
                    continue

                team1 = info.get(
                    "team1",
                    {}
                ) or {}

                team2 = info.get(
                    "team2",
                    {}
                ) or {}

                venue_info = info.get(
                    "venueInfo",
                    {}
                ) or {}

                matches.append({

                    "match_id": info.get(
                        "matchId"
                    ),

                    "series_id": series_id,

                    "series": series_name,

                    "match_type": match_type_name,

                    "description": info.get(
                        "matchDesc",
                        "Live Match"
                    ),

                    "format": info.get(
                        "matchFormat",
                        ""
                    ),

                    "state": info.get(
                        "state",
                        ""
                    ),

                    "status": info.get(
                        "status",
                        ""
                    ),

                    "team1": team1.get(
                        "teamName",
                        "Team 1"
                    ),

                    "team2": team2.get(
                        "teamName",
                        "Team 2"
                    ),

                    "team1_short": team1.get(
                        "teamSName",
                        ""
                    ),

                    "team2_short": team2.get(
                        "teamSName",
                        ""
                    ),

                    "venue": venue_info.get(
                        "ground",
                        ""
                    ),

                    "city": venue_info.get(
                        "city",
                        ""
                    )
                })

    return matches


def get_live_match_list():
    """
    Fetch live matches and return them as a flat list.
    """

    data = get_live_matches()

    return extract_live_matches(data)


# ============================================================
# LIVE TEAM NAMES
# ============================================================

def get_live_team_names():
    """
    Return unique teams currently involved in live matches.
    """

    matches = get_live_match_list()

    teams = set()

    for match in matches:

        team1 = match.get("team1")
        team2 = match.get("team2")

        if team1:
            teams.add(team1)

        if team2:
            teams.add(team2)

    return sorted(teams)


# ============================================================
# MATCH SCORECARD
# ============================================================

@st.cache_data(ttl=15)
def get_match_scorecard(match_id):
    """
    Fetch detailed scorecard for a match.
    """

    if not match_id:
        return {}

    data, _, _ = _get_json(
        "/matches/v1/get-scorecard-v2",
        params={
            "matchId": match_id
        }
    )

    return data


# ============================================================
# PLAYERS BY TEAM
# ============================================================

def get_players_by_team_name(team_name, db_conn=None):
    """
    Fetch team players using the Cricbuzz API.

    Falls back to SQLite if the API does not return players.
    """

    if not team_name:
        return []

    clean_name = team_name.strip()

    if clean_name in [
        "-- Select Team --",
        "-- Choose Team --",
        ""
    ]:
        return []

    headers = get_cricbuzz_headers()

    players = []

    # --------------------------------------------------------
    # 1. TRY CRICBUZZ API
    # --------------------------------------------------------

    if headers.get("x-rapidapi-key"):

        try:

            search_url = (
                f"{API_BASE_URL}/teams/v1/search"
            )

            response = requests.get(
                search_url,
                headers=headers,
                params={
                    "teamName": clean_name
                },
                timeout=8
            )

            if response.status_code == 200:

                data = response.json()

                teams_list = (
                    data.get("list", [])
                    or data.get("teams", [])
                )

                team_id = None

                for team in teams_list:

                    api_team_name = team.get(
                        "teamName",
                        ""
                    )

                    if (
                        api_team_name.strip().lower()
                        == clean_name.lower()
                    ):
                        team_id = team.get(
                            "teamId"
                        )
                        break

                if not team_id and teams_list:

                    team_id = teams_list[0].get(
                        "teamId"
                    )

                # ------------------------------------------------
                # FETCH TEAM SQUAD
                # ------------------------------------------------

                if team_id:

                    squad_url = (
                        f"{API_BASE_URL}/teams/v1/"
                        f"{team_id}/squad"
                    )

                    squad_response = requests.get(
                        squad_url,
                        headers=headers,
                        timeout=8
                    )

                    if squad_response.status_code == 200:

                        squad_json = (
                            squad_response.json()
                        )

                        squad_list = (
                            squad_json.get(
                                "squad",
                                []
                            )
                            or squad_json.get(
                                "player",
                                []
                            )
                            or squad_json.get(
                                "players",
                                []
                            )
                        )

                        for player in squad_list:

                            player_name = (
                                player.get("name")
                                or player.get("fullName")
                            )

                            if player_name:

                                players.append(
                                    player_name
                                )

        except requests.RequestException as e:

            print(
                f"API squad search failed: {e}"
            )

    # --------------------------------------------------------
    # 2. SQLITE FALLBACK
    # --------------------------------------------------------

    if not players and db_conn:

        try:

            import pandas as pd

            query = """
                SELECT p.player_name
                FROM players p
                JOIN teams t
                    ON p.team_id = t.team_id
                WHERE LOWER(t.team_name) = LOWER(?)
            """

            local_df = pd.read_sql_query(
                query,
                db_conn,
                params=(clean_name,)
            )

            if not local_df.empty:

                players = (
                    local_df[
                        "player_name"
                    ].tolist()
                )

        except Exception as e:

            print(
                f"Local DB fallback failed: {e}"
            )

    return sorted(
        set(players)
    )