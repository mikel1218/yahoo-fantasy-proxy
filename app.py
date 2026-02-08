from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "Yahoo Fantasy proxy running"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/fangraphs/pitcher_skills")
def fangraphs_pitchers():
    url = (
        "https://www.fangraphs.com/leaders.aspx"
        "?pos=all&stats=pit&type=8"
    )

    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    if table is None:
        return jsonify({"error": "FanGraphs table not found"}), 500

    df = pd.read_html(StringIO(str(table)))[0]

    cols = ["Name", "K%", "BB%", "SwStr%", "GB%", "xFIP"]
    df = df[cols].dropna()

    return jsonify(df.head(50).to_dict(orient="records"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
