import os
import secrets
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "http://localhost:3000/api/auth/github/callback")

# Store for OAuth state (in production, use Redis or database)
oauth_states = {}


def get_github_auth_url() -> str:
    """Generate GitHub OAuth authorization URL."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"created_at": int(__import__("time").time())}
    
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_CALLBACK_URL,
        "scope": "repo user:email",
        "state": state,
    }
    
    import urllib.parse
    return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"


def exchange_github_code(code: str, state: str) -> Optional[dict]:
    """Exchange OAuth code for access token."""
    # Validate state
    if state not in oauth_states:
        return None
    
    # Check if state is expired (5 minutes)
    import time
    if time.time() - oauth_states[state]["created_at"] > 300:
        del oauth_states[state]
        return None
    
    del oauth_states[state]
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return None
    
    # Exchange code for token
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
    )
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    access_token = data.get("access_token")
    
    if not access_token:
        return None
    
    # Get user info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    if user_response.status_code != 200:
        return None
    
    user_data = user_response.json()
    
    # Get user email if not public
    email = user_data.get("email")
    if not email:
        email_response = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if email_response.status_code == 200:
            emails = email_response.json()
            for e in emails:
                if e.get("primary"):
                    email = e.get("email")
                    break
    
    return {
        "access_token": access_token,
        "user_id": str(user_data.get("id")),
        "username": user_data.get("login"),
        "email": email,
        "name": user_data.get("name"),
        "avatar_url": user_data.get("avatar_url"),
    }


def get_github_user_info(access_token: str) -> Optional[dict]:
    """Get detailed GitHub user info using access token."""
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    if response.status_code != 200:
        return None
    
    return response.json()
