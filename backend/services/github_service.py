import os
import time
from typing import Dict, Optional

from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _validate_repo_files(files: Dict[str, str]) -> Dict[str, str]:
    validated_files: Dict[str, str] = {}
    for path, content in files.items():
        clean_path = path.strip().replace("\\", "/")
        if not clean_path or clean_path.startswith("/") or ".." in clean_path.split("/"):
            continue
        validated_files[clean_path] = str(content)
    return validated_files


def create_github_repo(
    repo_name: str,
    files: Optional[Dict[str, str]] = None,
    html_code: Optional[str] = None,
    user_token: Optional[str] = None,
):
    """
    Creates a public GitHub repository and uploads website files.
    
    Args:
        repo_name: Name of the repository to create
        files: Dictionary of file paths to content
        html_code: HTML code (alternative to files dict)
        user_token: User's personal GitHub token (takes precedence over GITHUB_TOKEN)
    
    Returns:
        repo_url (str)
        repo_id (int)
        unique_repo_name (str)
    """
    # Use user's token if provided, otherwise fall back to system token
    token = user_token or GITHUB_TOKEN
    
    if not token:
        print("[ERROR] No GitHub token available. Please connect your GitHub account.")
        return None, None, None

    file_map = dict(files or {})
    if not file_map and html_code:
        file_map = {"index.html": html_code}

    file_map = _validate_repo_files(file_map)
    if "index.html" not in file_map:
        print("[ERROR] index.html is required to create website repository.")
        return None, None, None

    try:
        g = Github(token)
        user = g.get_user()

        clean_name = repo_name.replace(" ", "-").lower()
        unique_repo_name = f"{clean_name}-{int(time.time())}"

        repo = user.create_repo(
            name=unique_repo_name,
            description="Auto-generated startup website",
            private=False,
        )

        for path in sorted(file_map.keys()):
            repo.create_file(
                path=path,
                message=f"Add {path}",
                content=file_map[path],
                branch="main",
            )

        print(f"[INFO] GitHub repo created with {len(file_map)} files:\n{repo.html_url}")
        return repo.html_url, repo.id, unique_repo_name

    except GithubException as e:
        print(f"[ERROR] GitHub repo creation failed:\n{e}")
        return None, None, None
