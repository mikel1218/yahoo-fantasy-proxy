from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import os

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyCoachBot/1.0)"
}

@app.route("/")
def home():
    return jsonify({"status": "Yahoo Fantasy proxy running"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ---------------------------
# FAN GRAPHS — PITCHERS
# ---------------------------
@app.route("/fangraphs/pitcher_skills")
def fangraphs_pitchers():
    try:
        url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&type=8"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")
        parsed_tables = []

        for table in tables:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                parsed_tables.append(df)
            except Exception:
                continue

        df = max(parsed_tables, key=lambda x: x.shape[1])

        def find_col(keyword):
            for col in df.columns:
                if keyword.lower() in str(col).lower():
                    return col
            return None

        col_map = {
            "Name": find_col("Name"),
            "K/9": find_col("K/9"),
            "BB/9": find_col("BB/9"),
            "GB%": find_col("GB%"),
            "xFIP": find_col("xFIP")
        }

        result = df[
            [
                col_map["Name"],
                col_map["K/9"],
                col_map["BB/9"],
                col_map["GB%"],
                col_map["xFIP"]
            ]
        ].dropna()

        result.columns = ["Name", "K_per_9", "BB_per_9", "GB_percent", "xFIP"]

        return jsonify(result.head(50).to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# FAN GRAPHS — HITTERS
# ---------------------------
@app.route("/fangraphs/hitter_skills")
def fangraphs_hitters():
    try:
        url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&type=8"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")
        parsed_tables = []

        for table in tables:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                parsed_tables.append(df)
            except Exception:
                continue

        df = max(parsed_tables, key=lambda x: x.shape[1])

        def find_col(keyword):
            for col in df.columns:
                if keyword.lower() in str(col).lower():
                    return col
            return None

        col_map = {
            "Name": find_col("Name"),
            "K%": find_col("K%"),
            "BB%": find_col("BB%"),
            "ISO": find_col("ISO"),
            "BABIP": find_col("BABIP"),
            "HardHit": find_col("Hard")
        }

        # remove missing metrics gracefully
        selected = [v for v in col_map.values() if v is not None]

        result = df[selected].dropna()

        # normalize column names
        result.columns = [
            "Name" if "name" in c.lower() else
            "K_percent" if "k%" in c.lower() else
            "BB_percent" if "bb%" in c.lower() else
            "ISO" if "iso" in c.lower() else
            "BABIP" if "babip" in c.lower() else
            "HardHit_percent"
            for c in result.columns
        ]

        return jsonify(result.head(50).to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
