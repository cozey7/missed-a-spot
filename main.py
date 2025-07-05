import requests
import secrets
import urllib.parse
import os

from flask import Flask, redirect, request, jsonify, session
from datetime import datetime, timedelta
from dotenv import load_dotenv

app = Flask(__name__)   # Instance of Flask object
app.secret_key = secrets.token_hex(16)  # Generate a secret 16-bit key

load_dotenv()

# Spotify API credentials
CLIENT_ID = '24d18580cf6b4e6a9bd5bfdccef3dbc8'
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000/callback'

# Spotify OAuth URLs
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'

@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'>Login with Spotify </a>"

@app.route('/login')
def login():
    scope = 'playlist-read-private playlist-modify-private user-read-private user-read-email'

    # Build the authorization URL
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)