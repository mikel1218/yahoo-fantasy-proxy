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

        if not parsed_tables:
            return jsonify({"error": "No parsable tables found"}), 500

        # Use the widest table = real leaderboard
        df = max(parsed_tables, key=lambda x: x.shape[1])

        # Column helpers
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

        missing = [k for k, v in col_map.items() if v is None]
        if missing:
            return jsonify({
                "error": "Required metrics not found",
                "missing_metrics": missing,
                "available_columns": list(df.columns)
            }), 500

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
        return jsonify({
            "error": "Unhandled exception",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
