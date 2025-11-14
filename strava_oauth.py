#!/usr/bin/env python3
"""
Strava OAuth flow helper script.
Run this to get your initial refresh token and access token.
"""

import requests
import webbrowser
from urllib.parse import urlparse, parse_qs
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost'

def get_authorization():
    """Step 1: Get authorization code from user."""
    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=activity:read_all,profile:read_all"
    )

    print("\n" + "="*80)
    print("STRAVA OAUTH SETUP")
    print("="*80)
    print("\n1. Opening browser to authorize access...")
    print(f"\nIf browser doesn't open, visit this URL:\n{auth_url}\n")

    webbrowser.open(auth_url)

    print("\n2. After authorizing, you'll be redirected to a localhost URL.")
    print("   Copy the ENTIRE URL from your browser's address bar and paste it here.")
    print("\n   It will look like: http://localhost/?state=&code=XXXXX&scope=read,activity:read_all\n")

    redirect_response = input("Paste the redirect URL here: ").strip()

    # Parse the authorization code from the URL
    parsed = urlparse(redirect_response)
    params = parse_qs(parsed.query)

    if 'code' not in params:
        print("\nError: No authorization code found in URL. Please try again.")
        return None

    return params['code'][0]


def exchange_token(auth_code):
    """Step 2: Exchange authorization code for access and refresh tokens."""
    print("\n3. Exchanging authorization code for tokens...")

    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code'
        }
    )

    if response.status_code != 200:
        print(f"\nError getting tokens: {response.status_code}")
        print(response.text)
        return None

    return response.json()


def save_tokens(token_data):
    """Save tokens to .env file."""
    print("\n4. Saving tokens to .env file...")

    # Read current .env
    with open('.env', 'r') as f:
        lines = f.readlines()

    # Update tokens
    new_lines = []
    for line in lines:
        if line.startswith('STRAVA_ACCESS_TOKEN='):
            new_lines.append(f"STRAVA_ACCESS_TOKEN={token_data['access_token']}\n")
        elif line.startswith('STRAVA_REFRESH_TOKEN='):
            new_lines.append(f"STRAVA_REFRESH_TOKEN={token_data['refresh_token']}\n")
        else:
            new_lines.append(line)

    # Write back
    with open('.env', 'w') as f:
        f.writelines(new_lines)

    print("\n" + "="*80)
    print("SUCCESS! Tokens saved to .env file")
    print("="*80)
    print(f"\nAccess Token: {token_data['access_token'][:20]}...")
    print(f"Refresh Token: {token_data['refresh_token'][:20]}...")
    print(f"Expires at: {token_data['expires_at']}")
    print(f"\nAthlete: {token_data['athlete']['firstname']} {token_data['athlete']['lastname']}")


if __name__ == '__main__':
    # Get authorization code
    auth_code = get_authorization()
    if not auth_code:
        exit(1)

    # Exchange for tokens
    token_data = exchange_token(auth_code)
    if not token_data:
        exit(1)

    # Save tokens
    save_tokens(token_data)

    print("\n✓ You're all set! Run 'python strava_test.py' to fetch your activities.\n")
