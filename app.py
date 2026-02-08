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

        if response.status_code != 200:
            return jsonify({
                "error": "FanGraphs request failed",
                "status_code": response.status_code
            }), 500

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")

        if table is None:
            return jsonify({
                "error": "FanGraphs table not found",
                "hint": "Page structure may have changed"
            }), 500

        df = pd.read_html(StringIO(str(table)))[0]

        expected_cols = ["Name", "K%", "BB%", "SwStr%", "GB%", "xFIP"]
        missing = [c for c in expected_cols if c not in df.columns]

        if missing:
            return jsonify({
                "error": "Expected columns missing",
                "missing_columns": missing,
                "available_columns": list(df.columns)
            }), 500

        df = df[expected_cols].dropna()

        return jsonify(df.head(50).to_dict(orient="records"))

    except Exception as e:
        return jsonify({
            "error": "Unhandled exception",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
