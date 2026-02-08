from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import os
from datetime import datetime, timedelta

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyCoachBot/1.0)"
}

# ======================================================
# BASIC HEALTH
# ======================================================
@app.route("/")
def home():
    return jsonify({"status": "Fantasy middleware running"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ======================================================
# FAN GRAPHS — PITCHERS
# ======================================================
@app.route("/fangraphs/pitcher_skills")
def fangraphs_pitchers():
    try:
        url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&type=8"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")
        dfs = []

        for table in tables:
            try:
                dfs.append(pd.read_html(StringIO(str(table)))[0])
            except Exception:
                continue

        df = max(dfs, key=lambda x: x.shape[1])

        def find_col(key):
            for c in df.columns:
                if key.lower() in str(c).lower():
                    return c
            return None

        result = df[
            [
                find_col("Name"),
                find_col("K/9"),
                find_col("BB/9"),
                find_col("GB%"),
                find_col("xFIP"),
            ]
        ].dropna()

        result.columns = [
            "Name",
            "K_per_9",
            "BB_per_9",
            "GB_percent",
            "xFIP",
        ]

        return jsonify(result.head(50).to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
# FAN GRAPHS — HITTERS
# ======================================================
@app.route("/fangraphs/hitter_skills")
def fangraphs_hitters():
    try:
        url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&type=8"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")
        dfs = []

        for table in tables:
            try:
                dfs.append(pd.read_html(StringIO(str(table)))[0])
            except Exception:
                continue

        df = max(dfs, key=lambda x: x.shape[1])

        def find_col(key):
            for c in df.columns:
                if key.lower() in str(c).lower():
                    return c
            return None

        result = df[
            [
                find_col("Name"),
                find_col("K%"),
                find_col("BB%"),
                find_col("ISO"),
                find_col("BABIP"),
            ]
        ].dropna()

        result.columns = [
            "Name",
            "K_percent",
            "BB_percent",
            "ISO",
            "BABIP",
        ]

        return jsonify(result.head(50).to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
# MLB STATS API — SCHEDULE & USAGE
# ======================================================

# ---- Smart Weekly Schedule (handles offseason) ----
@app.route("/mlb/week_schedule")
def mlb_week_schedule():
    start = datetime.utcnow().date()
    end = start + timedelta(days=7)

    def fetch_schedule(start_date, end_date):
        url = (
            "https://statsapi.mlb.com/api/v1/schedule"
            f"?sportId=1&startDate={start_date}&endDate={end_date}"
        )
        return requests.get(url).json()

    data = fetch_schedule(start, end)

    # If no games (offseason / pre-season), widen window
    if not data.get("dates"):
        end = start + timedelta(days=30)
        data = fetch_schedule(start, end)

    return data


# ---- Probable Starters (weekly SP planning) ----
@app.route("/mlb/probable_starters")
def mlb_probable_starters():
    url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        "?sportId=1&hydrate=probablePitcher"
    )
    data = requests.get(url).json()

    starters = []

    for date in data.get("dates", []):
        for game in date.get("games", []):
            for side in ["home", "away"]:
                team = game["teams"][side]
                pitcher = team.get("probablePitcher")
                if pitcher:
                    starters.append({
                        "date": date["date"],
                        "team": team["team"]["name"],
                        "pitcher": pitcher["fullName"],
                        "pitcher_id": pitcher["id"]
                    })

    return jsonify(starters)


# ---- Player Search (name → MLB ID) ----
@app.route("/mlb/player/<name>")
def mlb_player_lookup(name):
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={name}"
    return requests.get(url).json()


# ---- Pitcher Game Logs (workload & risk) ----
@app.route("/mlb/pitcher_usage/<int:player_id>")
def mlb_pitcher_usage(player_id):
    url = (
        "https://statsapi.mlb.com/api/v1/people/"
        f"{player_id}/stats?stats=gameLog&group=pitching"
    )
    return requests.get(url).json()


# ---- Team Roster (bullpen & rotation context) ----
@app.route("/mlb/team_roster/<int:team_id>")
def mlb_team_roster(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    return requests.get(url).json()


# ======================================================
# APP ENTRYPOINT
# ======================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
