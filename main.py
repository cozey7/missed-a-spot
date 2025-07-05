import requests
import secrets
import urllib.parse
import os

from flask import Flask, redirect, request, jsonify, session, Response
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
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'

@app.route('/')
def index() -> str:
    if 'access_token' in session:
        return f'''
            <h1>Welcome to my Spotify App</h1>
            <p>You are logged in!</p>
            <p><a href="/playlists">View Playlists</a></p>
            <p><a href="/logout">Logout</a></p>
            <p><a href="/refres-token"Refresh token</a></p>
            '''
    else:
        return '''
        <h1>My Spotify App</h1>
        <p>Please log in to continue</p>
        <p><a href="/login">Login with Spotify</a></p>
        '''


@app.route('/login')
def login():
    scope = 'user-library-read playlist-read-private playlist-modify-private user-read-private user-read-email'

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


@app.route('/callback')
def callback():
    if 'error' in request.args:
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

    # Store token data in session
    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

    return redirect('/')




@app.route('/playlists')
def get_playlists():
    response, error = make_spotify_request('me/playlists') # type: ignore

    # Check if there was an error
    if error:
        return f"Error: {error}"
    
    # Check if response is None (shouldn't happen if error is None, but good to be safe)
    if response is None:
        return "Error: No response received"
    
    # Check HTTP status
    if response.status_code != 200:
        return f"Error fetching playlists: {response.text}"

    playlists = response.json()

    return jsonify(playlists)



@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    # Refresh the access token
    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
    new_token_info = response.json()

    if response.status_code != 200:
        return redirect('/logout')

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']
    
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# Helper function to make all requests
def make_spotify_request(endpoint, method='GET', data=None):
    if 'access_token' not in session:
        return redirect('/login')
    
    # Refresh token if necessary
    if datetime.now().timestamp() >= session['expires_at']:
        refresh_result = refresh_token()
        if refresh_result:
            return None, "Token refresh failed"
        else:
            return None, "Token expired and no refresh token"

    
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }

    url = f"{SPOTIFY_API_BASE_URL}/{endpoint}"

    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    else:
        return None, f"Unsupported method: {method}"
    
    return response, None

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)