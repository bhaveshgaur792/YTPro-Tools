from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
import json
import re
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CACHE_FILE = "cache.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def normalize_youtube_url(url):
    """Handle all YouTube URL formats"""
    patterns = [
        (r'(https?://youtu\.be/)([\w-]+)', 'https://www.youtube.com/watch?v={}'),
        (r'(https?://(?:www\.|m\.)?youtube\.com/shorts/)([\w-]+)', 'https://www.youtube.com/watch?v={}'),
        (r'(https?://(?:www\.|m\.)?youtube\.com/embed/)([\w-]+)', 'https://www.youtube.com/watch?v={}'),
        (r'(https?://(?:www\.|m\.)?youtube\.com/watch\?v=)([\w-]+)', 'https://www.youtube.com/watch?v={}')
    ]
    
    for pattern, template in patterns:
        match = re.search(pattern, url)
        if match:
            return template.format(match.group(2))
    return url.split('?')[0]

def extract_views(soup):
    """Multi-method view extraction"""
    # Method 1: From metadata
    meta_view = soup.find("meta", {"itemprop": "interactionCount"})
    if meta_view:
        return f"{int(meta_view['content']):,}"
    
    # Method 2: From visible text
    view_text = soup.find("span", string=re.compile(r'views', re.IGNORECASE))
    if view_text:
        return view_text.text.split()[0]
    
    return "N/A"

def extract_channel(soup):
    """Robust channel extraction"""
    channel = soup.find("span", {"itemprop": "author"}).find("link", {"itemprop": "name"})
    return channel["content"] if channel else "N/A"

def extract_duration(soup):
    """Duration from multiple sources"""
    # Method 1: Video player duration
    duration = soup.find("span", {"class": "ytp-time-duration"})
    # Method 2: Mobile/alternative layout
    if not duration:
        duration = soup.find("div", {"id": "timestamp"})
    return duration.text if duration else "N/A"

def extract_tags(soup):
    """Extract tags from JSON-LD data"""
    script = soup.find("script", {"type": "application/ld+json"})
    if script:
        try:
            data = json.loads(script.text)
            return data.get("keywords", [])[:5]
        except:
            pass
    return []

def scrape_youtube(url):
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return {
            "title": soup.find("meta", {"name": "title"})["content"],
            "views": extract_views(soup),
            "channel": extract_channel(soup),
            "duration": extract_duration(soup),
            "thumbnail": soup.find("meta", {"property": "og:image"})["content"],
            "tags": extract_tags(soup)
        }
    except Exception as e:
        return {"error": f"Failed to analyze video: {str(e)}"}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        url = request.form["url"]
        clean_url = normalize_youtube_url(url)
        return jsonify(scrape_youtube(clean_url))
    except KeyError:
        return jsonify({"error": "No URL provided"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=False)
