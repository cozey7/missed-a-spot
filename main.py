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
REDIRECT_URI = 'http://127.0.0.1:5000/callback'

# Spotify OAuth URLs
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1/'

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
    print("Logging in...")
    return redirect(auth_url)


@app.route('/callback')
def callback():
    print('Reached callback')
    if 'error' in request.args:
        print('error json')
        return jsonify({"error": request.args['error']})
    
    # Get authorization code
    code = request.args['code']
    if not code:
        return "Error: No authorization code received"
    
    # Exchange authorization code for access token
    req_body = {
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']


    return redirect('/playlists')


@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    print(SPOTIFY_API_BASE_URL + 'me/playlists')
    response = requests.get(SPOTIFY_API_BASE_URL + 'me/playlists', headers=headers)
    print(response)
    playlists = response.json()

    return playlists



@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    

    if datetime.now().timestamp() <= session['expires_at']:
        return redirect('/playlists')


    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
    new_token_info = response.json()

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/playlists')
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)