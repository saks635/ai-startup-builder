import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from job_queue import RedisJobQueue
from storage import MongoStorage
from workflows.startup_workflow import run_startup_workflow

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_TTL_SECONDS = 60 * 60 * 12
PASSWORD_ITERATIONS = 120_000
JOB_LIST_LIMIT = int(os.getenv("JOB_LIST_LIMIT", "100"))


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=128)


class RunWorkflowRequest(BaseModel):
    startup_idea: str = Field(min_length=10, max_length=4000)


class OAuthCompleteSignupRequest(BaseModel):
    email: str
    password: str
    name: str
    github_access_token: Optional[str] = None
    github_username: Optional[str] = None
    vercel_access_token: Optional[str] = None
    vercel_team_id: Optional[str] = None


class AuthUser(BaseModel):
    id: str
    name: str
    email: str


storage = MongoStorage()
job_queue = RedisJobQueue()
worker_thread: Optional[threading.Thread] = None
worker_lock = threading.Lock()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return digest.hex()


def _make_password_record(password: str) -> Dict[str, str]:
    salt_hex = secrets.token_hex(16)
    return {
        "salt": salt_hex,
        "hash": _hash_password(password, salt_hex),
    }


def _create_jwt(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signed_payload = dict(payload)
    signed_payload["exp"] = int(time.time()) + JWT_TTL_SECONDS

    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(signed_payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}"

    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature_part = _b64url_encode(signature)
    return f"{signing_input}.{signature_part}"


def _decode_jwt(token: str) -> Dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid token format.") from e

    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    expected_signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    provided_signature = _b64url_decode(signature_part)

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(status_code=401, detail="Invalid token signature.")

    payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired.")
    return payload


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _serialize_user(user_record: Dict[str, Any]) -> AuthUser:
    return AuthUser(
        id=user_record["id"],
        name=user_record["name"],
        email=user_record["email"],
    )


def _require_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token.")

    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


def _default_action_plan(startup_idea: str) -> list[str]:
    short_idea = startup_idea.strip().split("\n")[0][:90]
    return [
        f"Define MVP scope for: {short_idea}",
        "Validate demand with 10-15 target user interviews this week.",
        "Build and publish the first landing page and capture signups.",
        "Launch a 2-week acquisition test with 2 channels and track CAC.",
        "Prioritize roadmap using user feedback and conversion metrics.",
    ]


def _serialize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": job["id"],
        "status": job["status"],
        "startup_idea": job["startup_idea"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "error": job.get("error"),
        "result": job.get("result"),
    }


def _safe_json_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        json.dumps(payload)
        return payload
    except TypeError:
        return json.loads(json.dumps(payload, default=str))


def _run_workflow_background(job_id: str) -> None:
    now = int(time.time())
    marked = storage.mark_job_running_if_queued(job_id, updated_at=now)
    if not marked:
        return

    job = storage.get_job(job_id)
    if not job:
        return

    # Get user to access their GitHub/Vercel tokens
    user = storage.get_user_by_id(job.get("user_id"))
    user_github_token = user.get("github_access_token") if user else None
    user_vercel_token = user.get("vercel_access_token") if user else None
    user_vercel_team_id = user.get("vercel_team_id") if user else None

    try:
        workflow_result = run_startup_workflow(
            job["startup_idea"],
            user_github_token=user_github_token,
            user_vercel_token=user_vercel_token,
            user_vercel_team_id=user_vercel_team_id,
        )
        result_payload = {
            "startup_analysis": workflow_result.get("analysis_result"),
            "market_insights": workflow_result.get("research_result"),
            "action_plan": workflow_result.get("action_plan") or _default_action_plan(job["startup_idea"]),
            "generated_website_files": workflow_result.get("generated_files", []),
            "generated_website_repo": workflow_result.get("repo_url"),
            "github_repository_link": workflow_result.get("repo_url"),
            "vercel_deployment_link": workflow_result.get("live_url"),
            "workflow_raw": workflow_result,
        }
        storage.mark_job_completed(
            job_id,
            updated_at=int(time.time()),
            result_payload=_safe_json_payload(result_payload),
        )
    except Exception as exc:
        storage.mark_job_failed(job_id, updated_at=int(time.time()), error=str(exc))


def _run_worker_loop() -> None:
    while True:
        if not job_queue.is_available():
            time.sleep(2)
            continue

        try:
            job_id = job_queue.dequeue(timeout=5)
        except Exception:
            time.sleep(2)
            continue

        if not job_id:
            continue

        _run_workflow_background(job_id)


def _ensure_worker_thread() -> None:
    global worker_thread
    with worker_lock:
        if worker_thread and worker_thread.is_alive():
            return
        worker_thread = threading.Thread(target=_run_worker_loop, daemon=True)
        worker_thread.start()


def _recover_pending_jobs() -> None:
    now = int(time.time())
    storage.reset_running_jobs_to_queued(updated_at=now)
    pending_job_ids = storage.list_pending_job_ids(limit=500)
    if pending_job_ids and job_queue.is_available():
        try:
            job_queue.enqueue_many(pending_job_ids)
        except Exception:
            pass


app = FastAPI(
    title="AI Startup Builder API",
    version="1.2.0",
    description="Auth + workflow API with OAuth2 support for GitHub and Vercel",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.on_event("startup")
def on_startup() -> None:
    storage.init_schema()
    _recover_pending_jobs()
    _ensure_worker_thread()


@app.get("/")
def root():
    if FRONTEND_DIR.exists():
        return RedirectResponse(url="/app/login.html")
    return {"message": "API is running.", "frontend_path": str(FRONTEND_DIR)}


@app.get("/api/health")
def health():
    database_connected = storage.is_available()
    return {
        "status": "ok" if database_connected else "degraded",
        "timestamp": int(time.time()),
        "database": "connected" if database_connected else "unavailable",
        "redis_queue_available": job_queue.is_available(),
    }


# ============== OAuth Endpoints ==============

@app.get("/api/auth/github/login")
def github_login():
    """Initiate GitHub OAuth login - returns auth URL."""
    from services.github_oauth import get_github_auth_url
    
    # Check if OAuth is configured
    if not os.getenv("GITHUB_CLIENT_ID") or not os.getenv("GITHUB_CLIENT_SECRET"):
        return {"error": "GitHub OAuth not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env"}
    
    auth_url = get_github_auth_url()
    return {"auth_url": auth_url}


@app.get("/api/auth/github/callback")
def github_callback(code: str = Query(None), state: str = Query(None)):
    """Handle GitHub OAuth callback."""
    from services.github_oauth import exchange_github_code
    
    if not code or not state:
        return {"error": "Missing code or state parameter"}
    
    user_data = exchange_github_code(code, state)
    if not user_data:
        return {"error": "Failed to exchange code for token"}
    
    # Check if user already exists
    existing_user = storage.get_user_by_email(user_data.get("email", ""))
    
    if existing_user:
        # Update existing user with GitHub token
        storage.update_user_github_token(
            user_id=existing_user["id"],
            github_access_token=user_data["access_token"],
            github_username=user_data["username"],
        )
        token = _create_jwt({"sub": existing_user["id"], "email": existing_user["email"]})
        # Redirect to frontend with token
        return RedirectResponse(url=f"/app/dashboard?token={token}&github_connected=true")
    else:
        # New user - redirect to frontend with OAuth data to complete signup
        import urllib.parse
        params = urllib.parse.urlencode({
            "github_token": user_data["access_token"],
            "github_username": user_data["username"],
            "github_email": user_data.get("email", ""),
            "github_name": user_data.get("name", ""),
        })
        return RedirectResponse(url=f"/app/signup?{params}")


@app.get("/api/auth/vercel/login")
def vercel_login():
    """Initiate Vercel OAuth login - returns auth URL."""
    from services.vercel_oauth import get_vercel_auth_url
    
    # Check if OAuth is configured
    if not os.getenv("VERCEL_CLIENT_ID") or not os.getenv("VERCEL_CLIENT_SECRET"):
        return {"error": "Vercel OAuth not configured. Please set VERCEL_CLIENT_ID and VERCEL_CLIENT_SECRET in .env"}
    
    auth_url = get_vercel_auth_url()
    return {"auth_url": auth_url}


@app.get("/api/auth/vercel/callback")
def vercel_callback(code: str = Query(None), state: str = Query(None)):
    """Handle Vercel OAuth callback."""
    from services.vercel_oauth import exchange_vercel_code
    
    if not code or not state:
        return {"error": "Missing code or state parameter"}
    
    user_data = exchange_vercel_code(code, state)
    if not user_data:
        return {"error": "Failed to exchange code for token. Note: Vercel OAuth requires partner setup."}
    
    # Return OAuth data for frontend to handle (user must be logged in)
    import urllib.parse
    params = urllib.parse.urlencode({
        "vercel_token": user_data["access_token"],
        "vercel_email": user_data.get("email", ""),
        "vercel_name": user_data.get("name", ""),
    })
    return RedirectResponse(url=f"/app/dashboard?{params}")


@app.post("/api/auth/oauth/complete-signup")
def complete_oauth_signup(payload: OAuthCompleteSignupRequest):
    """Complete signup after OAuth flow."""
    email = _normalize_email(payload.email)
    existing_user = storage.get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered.")
    
    password_record = _make_password_record(payload.password)
    user_id = f"user_{secrets.token_hex(8)}"
    user_record = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email,
        "password_hash": password_record["hash"],
        "password_salt": password_record["salt"],
        "created_at": int(time.time()),
    }
    storage.create_user(
        user_id=user_record["id"],
        name=user_record["name"],
        email=user_record["email"],
        password_hash=user_record["password_hash"],
        password_salt=user_record["password_salt"],
        created_at=user_record["created_at"],
    )
    
    # Save OAuth tokens
    if payload.github_access_token and payload.github_username:
        storage.update_user_github_token(
            user_id=user_id,
            github_access_token=payload.github_access_token,
            github_username=payload.github_username,
        )
    
    if payload.vercel_access_token:
        storage.update_user_vercel_token(
            user_id=user_id,
            vercel_access_token=payload.vercel_access_token,
            vercel_team_id=payload.vercel_team_id,
        )
    
    token = _create_jwt({"sub": user_id, "email": email})
    return {
        "token": token,
        "user": _serialize_user(user_record).model_dump(),
        "github_connected": bool(payload.github_access_token),
        "github_username": payload.github_username,
        "vercel_connected": bool(payload.vercel_access_token),
    }


# ============== Regular Auth Endpoints ==============

@app.post("/api/auth/signup")
def signup(payload: SignupRequest):
    email = _normalize_email(payload.email)
    existing_user = storage.get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered.")

    password_record = _make_password_record(payload.password)
    user_id = f"user_{secrets.token_hex(8)}"
    user_record = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email,
        "password_hash": password_record["hash"],
        "password_salt": password_record["salt"],
        "created_at": int(time.time()),
    }
    storage.create_user(
        user_id=user_record["id"],
        name=user_record["name"],
        email=user_record["email"],
        password_hash=user_record["password_hash"],
        password_salt=user_record["password_salt"],
        created_at=user_record["created_at"],
    )

    token = _create_jwt({"sub": user_record["id"], "email": user_record["email"]})
    return {"token": token, "user": _serialize_user(user_record).model_dump()}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    email = _normalize_email(payload.email)
    user = storage.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    provided_hash = _hash_password(payload.password, user["password_salt"])
    if not hmac.compare_digest(provided_hash, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _create_jwt({"sub": user["id"], "email": user["email"]})
    return {
        "token": token, 
        "user": _serialize_user(user).model_dump(),
        "github_connected": bool(user.get("github_access_token")),
        "github_username": user.get("github_username"),
        "vercel_connected": bool(user.get("vercel_access_token")),
    }


@app.get("/api/auth/me")
def me(current_user: Dict[str, Any] = Depends(_require_current_user)):
    return {
        "user": _serialize_user(current_user).model_dump(),
        "github_connected": bool(current_user.get("github_access_token")),
        "github_username": current_user.get("github_username"),
        "vercel_connected": bool(current_user.get("vercel_access_token")),
    }


# ============== Integration Connect/Disconnect ==============

@app.post("/api/integrations/github/connect")
def connect_github(payload: dict, current_user: Dict[str, Any] = Depends(_require_current_user)):
    """Connect GitHub using a personal access token (alternative to OAuth)."""
    from github import Github
    from github.GithubException import GithubException
    
    github_token = payload.get("github_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="github_token required")
    
    try:
        g = Github(github_token)
        gh_user = g.get_user()
        username = gh_user.login
        
        storage.update_user_github_token(
            user_id=current_user["id"],
            github_access_token=github_token,
            github_username=username,
        )
        
        return {
            "success": True,
            "github_username": username,
            "message": "GitHub connected successfully!"
        }
    except GithubException as e:
        raise HTTPException(status_code=400, detail=f"Invalid GitHub token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect GitHub: {str(e)}")


@app.post("/api/integrations/vercel/connect")
def connect_vercel(payload: dict, current_user: Dict[str, Any] = Depends(_require_current_user)):
    """Connect Vercel using an API token (alternative to OAuth)."""
    import requests
    
    vercel_token = payload.get("vercel_token")
    if not vercel_token:
        raise HTTPException(status_code=400, detail="vercel_token required")
    
    headers = {"Authorization": f"Bearer {vercel_token}"}
    try:
        response = requests.get("https://api.vercel.com/v6/user", headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Vercel token")
        
        vercel_data = response.json()
        
        storage.update_user_vercel_token(
            user_id=current_user["id"],
            vercel_access_token=vercel_token,
            vercel_team_id=payload.get("vercel_team_id"),
        )
        
        return {
            "success": True,
            "vercel_account": vercel_data.get("user", {}).get("name") or vercel_data.get("user", {}).get("email"),
            "message": "Vercel connected successfully!"
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect Vercel: {str(e)}")


@app.post("/api/integrations/github/disconnect")
def disconnect_github(current_user: Dict[str, Any] = Depends(_require_current_user)):
    """Disconnect GitHub account."""
    storage.update_user_github_token(
        user_id=current_user["id"],
        github_access_token="",
        github_username="",
    )
    return {"success": True, "message": "GitHub disconnected."}


@app.post("/api/integrations/vercel/disconnect")
def disconnect_vercel(current_user: Dict[str, Any] = Depends(_require_current_user)):
    """Disconnect Vercel account."""
    storage.update_user_vercel_token(
        user_id=current_user["id"],
        vercel_access_token="",
        vercel_team_id=None,
    )
    return {"success": True, "message": "Vercel disconnected."}


# ============== Workflow Endpoints ==============

@app.post("/api/workflow/run")
def run_workflow(payload: RunWorkflowRequest, current_user: Dict[str, Any] = Depends(_require_current_user)):
    now = int(time.time())
    job_id = f"job_{secrets.token_hex(8)}"
    storage.create_job(
        job_id=job_id,
        user_id=current_user["id"],
        startup_idea=payload.startup_idea.strip(),
        status="queued",
        created_at=now,
        updated_at=now,
    )

    enqueued = False
    if job_queue.is_available():
        try:
            job_queue.enqueue(job_id)
            enqueued = True
        except Exception:
            enqueued = False

    if not enqueued:
        thread = threading.Thread(target=_run_workflow_background, args=(job_id,), daemon=True)
        thread.start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/workflow/jobs")
def list_jobs(current_user: Dict[str, Any] = Depends(_require_current_user)):
    user_jobs = storage.list_jobs_for_user(current_user["id"], limit=JOB_LIST_LIMIT)
    return {"jobs": [_serialize_job(job) for job in user_jobs]}


@app.get("/api/workflow/jobs/{job_id}")
def get_job(job_id: str, current_user: Dict[str, Any] = Depends(_require_current_user)):
    job = storage.get_job_for_user(job_id, current_user["id"])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _serialize_job(job)


@app.get("/api/docs/endpoints")
def docs_endpoints():
    return {
        "auth": {
            "POST /api/auth/signup": "Create account with email/password",
            "POST /api/auth/login": "Login with email/password",
            "GET /api/auth/me": "Get current user info",
            "GET /api/auth/github/login": "Start GitHub OAuth",
            "GET /api/auth/github/callback": "GitHub OAuth callback",
            "GET /api/auth/vercel/login": "Start Vercel OAuth",
            "GET /api/auth/vercel/callback": "Vercel OAuth callback",
            "POST /api/auth/oauth/complete-signup": "Complete signup after OAuth",
        },
        "integrations": {
            "POST /api/integrations/github/connect": "Connect GitHub with token",
            "POST /api/integrations/vercel/connect": "Connect Vercel with token",
            "POST /api/integrations/github/disconnect": "Disconnect GitHub",
            "POST /api/integrations/vercel/disconnect": "Disconnect Vercel",
        },
        "workflow": {
            "POST /api/workflow/run": "Submit startup idea",
            "GET /api/workflow/jobs": "List user jobs",
            "GET /api/workflow/jobs/{job_id}": "Get job status",
        },
    }
