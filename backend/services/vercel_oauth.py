import os
import secrets
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Vercel doesn't have traditional OAuth2 for end users
# They use API tokens. We'll simulate OAuth-like flow using Vercel's
# OAuth endpoint for Vercel CLI integration
VERCEL_CLIENT_ID = os.getenv("VERCEL_CLIENT_ID", "")
VERCEL_CLIENT_SECRET = os.getenv("VERCEL_CLIENT_SECRET", "")
VERCEL_CALLBACK_URL = os.getenv("VERCEL_CALLBACK_URL", "http://localhost:3000/api/auth/vercel/callback")

# Store for OAuth state
oauth_states = {}


def get_vercel_auth_url() -> str:
    """Generate Vercel OAuth authorization URL."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"created_at": int(__import__("time").time())}
    
    params = {
        "client_id": VERCEL_CLIENT_ID,
        "redirect_uri": VERCEL_CALLBACK_URL,
        "scope": "full",  # Full access to account
        "state": state,
    }
    
    import urllib.parse
    # Vercel's OAuth authorization URL
    return f"https://vercel.com/oauth/authorize?{urllib.parse.urlencode(params)}"


def exchange_vercel_code(code: str, state: str) -> Optional[dict]:
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
    
    if not VERCEL_CLIENT_ID or not VERCEL_CLIENT_SECRET:
        # Fallback: If no OAuth credentials, return None
        # Users will need to provide tokens manually
        return None
    
    # Exchange code for token
    response = requests.post(
        "https://api.vercel.com/oauth/access_token",
        data={
            "client_id": VERCEL_CLIENT_ID,
            "client_secret": VERCEL_CLIENT_SECRET,
            "code": code,
            "redirect_uri": VERCEL_CALLBACK_URL,
        },
    )
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    access_token = data.get("access_token")
    
    if not access_token:
        return None
    
    # Get user info
    user_response = requests.get(
        "https://api.vercel.com/v6/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    if user_response.status_code != 200:
        return None
    
    user_data = user_response.json()
    
    # Get teams
    teams_response = requests.get(
        "https://api.vercel.com/v6/teams",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    teams = []
    if teams_response.status_code == 200:
        teams_data = teams_response.json()
        teams = teams_data.get("teams", [])
    
    return {
        "access_token": access_token,
        "user_id": str(user_data.get("user", {}).get("uid") or user_data.get("user", {}).get("id")),
        "email": user_data.get("user", {}).get("email"),
        "name": user_data.get("user", {}).get("name"),
        "teams": teams,
    }


def get_vercel_user_info(access_token: str) -> Optional[dict]:
    """Get detailed Vercel user info using access token."""
    response = requests.get(
        "https://api.vercel.com/v6/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    if response.status_code != 200:
        return None
    
    return response.json()


def create_vercel_project(access_token: str, project_name: str, team_id: Optional[str] = None) -> Optional[dict]:
    """Create a new Vercel project."""
    headers = {"Authorization": f"Bearer {access_token}"}
    if team_id:
        headers["x-vercel-team-id"] = team_id
    
    response = requests.post(
        "https://api.vercel.com/v6/projects",
        headers=headers,
        json={"name": project_name},
    )
    
    if response.status_code not in [200, 201]:
        return None
    
    return response.json()
