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

def normalize_youtube_url(url):
    """Convert all YouTube URL formats to standard watch?v= format"""
    if "youtu.be" in url:
        # Handle shortened URLs
        video_id = url.split("/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    elif "/shorts/" in url:
        # Handle YouTube Shorts URLs
        video_id = url.split("/shorts/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    elif "embed/" in url:
        # Handle embedded player URLs
        video_id = url.split("embed/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        # Clean parameters from standard URLs
        return url.split("?")[0]

def get_text(soup, selector):
    """Safe element text extraction"""
    element = soup.select_one(selector)
    return element.text.strip() if element else "N/A"

def get_meta_content(soup, property_name):
    """Safe meta tag content extraction"""
    meta = soup.find("meta", {"property": property_name})
    return meta["content"] if meta else "N/A"

def extract_tags(soup):
    """Robust tag extraction from JSON"""
    try:
        script = soup.find("script", text=lambda t: t and '"keywords":[' in t)
        if script:
            json_text = script.text.split('"keywords":[')[1].split(']')[0]
            return [tag.strip('"') for tag in json_text.split(',')[:5]]
        return []
    except Exception as e:
        return []

def scrape_youtube(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        return {
            "title": get_meta_content(soup, "og:title"),
            "views": get_text(soup, "span.yt-core-attributed-string"),
            "channel": get_text(soup, "a.yt-simple-endpoint.style-scope.yt-formatted-string"),
            "duration": get_text(soup, "span.ytp-time-duration"),
            "thumbnail": get_meta_content(soup, "og:image"),
            "tags": extract_tags(soup)
        }
    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"})

    try:
        # Normalize URL before processing
        normalized_url = normalize_youtube_url(url)
        if "youtube.com/watch?v=" not in normalized_url:
            return jsonify({"error": "Invalid YouTube URL"})
            
        return jsonify(scrape_youtube(normalized_url))
    except Exception as e:
        return jsonify({"error": f"Invalid URL format: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
