from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
import json
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

CACHE_FILE = "cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(url, data):
    cache = load_cache()
    cache[url] = {
        **data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def scrape_youtube(url):
    cache = load_cache()
    if url in cache:
        return cache[url]

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        # Robust element extraction with fallbacks
        data = {
            "title": soup.find("meta", property="og:title")["content"] if soup.find("meta", property="og:title") else "No title",
            "views": soup.select_one(".watch-view-count").text.split()[0] if soup.select_one(".watch-view-count") else "N/A",
            "channel": soup.select_one("#channel-name a").text.strip() if soup.select_one("#channel-name a") else "No channel",
            "duration": soup.select_one(".ytp-time-duration").text if soup.select_one(".ytp-time-duration") else "00:00",
            "thumbnail": soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else "",
            "tags": extract_tags(soup)  # Separate function for reliability
        }
        
        save_cache(url, data)
        return data
    except Exception as e:
        return {"error": str(e)}

def extract_tags(soup):
    try:
        tags_script = soup.find("script", text=lambda t: t and "keywords" in t)
        if tags_script:
            return json.loads(
                tags_script.text.split('"keywords":[')[1].split(']')[0]
                .replace('"', '').split(',')[:5]
            )
        return []
    except:
        return []

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
    app.run(debug=True)
