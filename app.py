from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "Yahoo Fantasy proxy running"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from bs4 import BeautifulSoup
import pandas as pd l
from io import StringIO

@app.route("/fangraphs/pitcher_skills")
def fangraphs_pitchers():
    url = (
        "https://www.fangraphs.com/leaders.aspx"
        "?pos=all&stats=pit&type=8&season=2026"
    )
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    df = pd.read_html(StringIO(str(table)))[0]

    cols = ["Name", "K%", "BB%", "SwStr%", "GB%", "xFIP"]
    df = df[cols].dropna()

    return df.head(50).to_json(orient="records")
