import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_API_BASE = "https://api.vercel.com"


def _disable_vercel_auth_for_project(project_name: str, headers: dict) -> bool:
    """
    Disable Vercel Authentication protection for a project so URLs are publicly reachable.
    """
    try:
        response = requests.patch(
            f"{VERCEL_API_BASE}/v9/projects/{project_name}",
            headers=headers,
            json={"ssoProtection": None},
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"[WARN] Could not update Vercel project protection settings:\n{e}")
        return False

    if response.status_code not in [200, 201]:
        print("[WARN] Vercel project update did not disable protection.")
        print(response.text)
        return False

    return True


def deploy_to_vercel(
    project_name: str,
    repo_id: int,
    user_token: Optional[str] = None,
    vercel_team_id: Optional[str] = None,
):
    """
    Deploy a GitHub repository to Vercel as a production deployment.

    Args:
        project_name (str): The Vercel project name.
        repo_id (int): The numeric GitHub repository ID.
        user_token: User's personal Vercel token (takes precedence over VERCEL_TOKEN)
        vercel_team_id: Vercel team ID for team deployments

    Returns:
        live_url (str): Public deployment URL.
    """
    # Use user's token if provided, otherwise fall back to system token
    token = user_token or VERCEL_TOKEN
    
    if not token:
        print("[ERROR] No Vercel token available. Please connect your Vercel account.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Add team_id header if provided (for team deployments)
    if vercel_team_id:
        headers["x-vercel-team-id"] = vercel_team_id

    payload = {
        "name": project_name,
        "gitSource": {
            "type": "github",
            "repoId": repo_id,
            "ref": "main",
        },
        "projectSettings": {
            "framework": None,
        },
        "target": "production",
    }

    try:
        response = requests.post(
            f"{VERCEL_API_BASE}/v13/deployments?skipAutoDetectionConfirmation=1",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Vercel deployment request failed:\n{e}")
        if hasattr(e, "response") and e.response is not None:
            print("Response content:", e.response.text)
        return None

    deploy_data = response.json()
    raw_url = deploy_data.get("url")
    if not raw_url:
        print("[ERROR] Vercel deployment response missing 'url'.")
        print(deploy_data)
        return None

    live_url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

    if _disable_vercel_auth_for_project(project_name=project_name, headers=headers):
        print("[INFO] Disabled Vercel Authentication for this project.")
    else:
        print("[WARN] Project may still require Vercel login depending on team defaults.")

    print(f"[INFO] Public production Vercel URL: {live_url}")
    return live_url
