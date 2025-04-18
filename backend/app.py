import os
from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
import json
import re
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__,
    static_folder="../frontend/static",
    template_folder="../frontend/templates"
)

# Configuration
app.config.update({
    'CORS_HEADERS': 'Content-Type',
    'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
})

CORS(app, resources={r"/analyze": {"origins": "*"}})

# Constants
CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache.json")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
    r'(watch\?v=|shorts/|embed/|v/|.+[?&]v=)?([^&=%\?]{11})'
)

def normalize_youtube_url(url):
    """Normalize all YouTube URL formats to standard watch URL"""
    match = YOUTUBE_REGEX.search(url)
    if match:
        video_id = match.group(5)
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

def extract_metadata(soup):
    """Extract common metadata from video page"""
    return {
        "title": soup.find("meta", {"name": "title"})["content"],
        "channel": extract_channel(soup),
        "views": extract_views(soup),
        "duration": extract_duration(soup),
        "thumbnail": soup.find("meta", {"property": "og:image"})["content"],
        "tags": extract_tags(soup)
    }

def extract_channel(soup):
    """Extract channel information with fallbacks"""
    channel = soup.find("span", {"itemprop": "author"})
    return channel.find("link", {"itemprop": "name"})["content"] if channel else "N/A"

def extract_views(soup):
    """Multi-source view count extraction"""
    selectors = [
        {"name": "meta", "attrs": {"itemprop": "interactionCount"}},
        {"name": "span", "attrs": {"class": "view-count"}},
        {"name": "div", "attrs": {"id": "count"}}
    ]
    
    for selector in selectors:
        element = soup.find(selector["name"], selector.get("attrs"))
        if element:
            return element.text.strip() if element.text else element.get("content", "N/A")
    return "N/A"

@app.route("/")
def serve_frontend():
    """Serve main frontend interface"""
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_video():
    """Analyze YouTube video endpoint"""
    try:
        if 'url' not in request.form:
            return jsonify({"error": "Missing URL parameter"}), 400
            
        raw_url = request.form['url']
        clean_url = normalize_youtube_url(raw_url)
        
        if not clean_url:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9"
        }

        response = requests.get(clean_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        result = extract_metadata(soup)
        
        return jsonify(result)

    except requests.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 502
    except Exception as e:
        app.logger.error(f"Analysis error: {str(e)}")
        return jsonify({"error": "Failed to analyze video"}), 500

if __name__ == "__main__":
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )
