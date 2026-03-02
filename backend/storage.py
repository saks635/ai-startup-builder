import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError


DEFAULT_MONGODB_URL = "mongodb://127.0.0.1:27017"
DEFAULT_MONGODB_DB_NAME = "ai_startup_builder"


class MongoStorage:
    def __init__(self, mongodb_url: Optional[str] = None, db_name: Optional[str] = None):
        self.mongodb_url = mongodb_url or os.getenv("MONGODB_URL", DEFAULT_MONGODB_URL)
        parsed_db_name = self._extract_db_name(self.mongodb_url)
        self.db_name = db_name or parsed_db_name or os.getenv("MONGODB_DB_NAME", DEFAULT_MONGODB_DB_NAME)
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    @staticmethod
    def _extract_db_name(mongodb_url: str) -> Optional[str]:
        parsed = urlparse(mongodb_url)
        if not parsed.path or parsed.path == "/":
            return None
        return parsed.path.lstrip("/")

    def _ensure_client(self) -> None:
        if self._client is not None and self._db is not None:
            return
        self._client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
        self._db = self._client[self.db_name]

    @property
    def db(self) -> Database:
        self._ensure_client()
        assert self._db is not None
        return self._db

    @property
    def users(self) -> Collection:
        return self.db["users"]

    @property
    def jobs(self) -> Collection:
        return self.db["jobs"]

    def is_available(self) -> bool:
        try:
            self._ensure_client()
            assert self._client is not None
            self._client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def init_schema(self) -> None:
        self.users.create_index([("id", ASCENDING)], unique=True)
        self.users.create_index([("email", ASCENDING)], unique=True)

        self.jobs.create_index([("id", ASCENDING)], unique=True)
        self.jobs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        self.jobs.create_index([("status", ASCENDING), ("updated_at", DESCENDING)])
        self.jobs.create_index([("status", ASCENDING), ("created_at", ASCENDING)])

    def create_user(
        self,
        user_id: str,
        name: str,
        email: str,
        password_hash: str,
        password_salt: str,
        created_at: int,
    ) -> None:
        self.users.insert_one(
            {
                "id": user_id,
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "password_salt": password_salt,
                "created_at": created_at,
                # OAuth tokens for user-specific deployments
                "github_access_token": None,
                "github_username": None,
                "vercel_access_token": None,
                "vercel_team_id": None,
            }
        )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        row = self.users.find_one({"email": email}, {"_id": 0})
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = self.users.find_one({"id": user_id}, {"_id": 0})
        return dict(row) if row else None

    def update_user_github_token(
        self,
        user_id: str,
        github_access_token: str,
        github_username: str,
    ) -> bool:
        result = self.users.update_one(
            {"id": user_id},
            {"$set": {"github_access_token": github_access_token, "github_username": github_username}},
        )
        return result.modified_count == 1

    def update_user_vercel_token(
        self,
        user_id: str,
        vercel_access_token: str,
        vercel_team_id: Optional[str] = None,
    ) -> bool:
        result = self.users.update_one(
            {"id": user_id},
            {"$set": {"vercel_access_token": vercel_access_token, "vercel_team_id": vercel_team_id}},
        )
        return result.modified_count == 1

    def create_job(
        self,
        job_id: str,
        user_id: str,
        startup_idea: str,
        status: str,
        created_at: int,
        updated_at: int,
    ) -> None:
        self.jobs.insert_one(
            {
                "id": job_id,
                "user_id": user_id,
                "status": status,
                "startup_idea": startup_idea,
                "created_at": created_at,
                "updated_at": updated_at,
                "error": None,
                "result": None,
            }
        )

    def mark_job_running_if_queued(self, job_id: str, updated_at: int) -> bool:
        result = self.jobs.update_one(
            {"id": job_id, "status": "queued"},
            {"$set": {"status": "running", "updated_at": updated_at, "error": None}},
        )
        return result.modified_count == 1

    def mark_job_completed(self, job_id: str, updated_at: int, result_payload: Dict[str, Any]) -> None:
        self.jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "completed", "updated_at": updated_at, "error": None, "result": result_payload}},
        )

    def mark_job_failed(self, job_id: str, updated_at: int, error: str) -> None:
        self.jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "failed", "updated_at": updated_at, "error": error}},
        )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        row = self.jobs.find_one({"id": job_id})
        return self._serialize_job_row(row) if row else None

    def get_job_for_user(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        row = self.jobs.find_one({"id": job_id, "user_id": user_id})
        return self._serialize_job_row(row) if row else None

    def list_jobs_for_user(self, user_id: str, limit: int = 100) -> list[Dict[str, Any]]:
        rows = self.jobs.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(limit)
        return [self._serialize_job_row(row) for row in rows]

    def reset_running_jobs_to_queued(self, updated_at: int) -> int:
        result = self.jobs.update_many(
            {"status": "running"},
            {"$set": {"status": "queued", "updated_at": updated_at}},
        )
        return int(result.modified_count)

    def list_pending_job_ids(self, limit: int = 500) -> list[str]:
        rows = self.jobs.find({"status": "queued"}, {"id": 1, "_id": 0}).sort("created_at", ASCENDING).limit(limit)
        return [row["id"] for row in rows if row.get("id")]

    @staticmethod
    def _serialize_job_row(row: Any) -> Dict[str, Any]:
        as_dict = dict(row)
        as_dict.pop("_id", None)
        if "result_json" in as_dict and "result" not in as_dict:
            as_dict["result"] = as_dict.pop("result_json")
        as_dict.setdefault("result", None)
        return as_dict


# Backward-compatible alias to avoid touching external imports.
PostgresStorage = MongoStorage
