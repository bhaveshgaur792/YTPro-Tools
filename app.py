from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
import json
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CACHE_FILE = "cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(url, data):
    cache = load_cache()
    cache[url] = {**data, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def scrape_youtube(url):
    cache = load_cache()
    if url in cache:
        return cache[url]

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("meta", property="og:title")
        thumbnail = soup.find("meta", property="og:image")
        views = soup.select_one(".watch-view-count")
        channel = soup.select_one("#channel-name a")
        duration = soup.select_one(".ytp-time-duration")
        keywords_script = soup.find("script", text=lambda t: t and "keywords" in t)

        data = {
            "title": title["content"] if title else "N/A",
            "views": views.text.split()[0] if views else "N/A",
            "channel": channel.text.strip() if channel else "N/A",
            "duration": duration.text if duration else "N/A",
            "thumbnail": thumbnail["content"] if thumbnail else "N/A",
            "tags": []
        }

        if keywords_script:
            try:
                keywords_raw = keywords_script.text.split('"keywords":[')[1].split(']')[0]
                data["tags"] = keywords_raw.replace('"', '').split(',')[:5]
            except Exception:
                data["tags"] = []

        save_cache(url, data)
        return data

    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("url")
    if not url or "youtube.com" not in url:
        return jsonify({"error": "Invalid YouTube URL"})
    return jsonify(scrape_youtube(url))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
