# Backend API Endpoints

Base URL example: `http://127.0.0.1:8000`

## Authentication

### `POST /api/auth/signup`
Create a user and return JWT token.

Request:
```json
{
  "name": "Saksham",
  "email": "user@example.com",
  "password": "secret123"
}
```

Response:
```json
{
  "token": "<jwt>",
  "user": {
    "id": "user_xxx",
    "name": "Saksham",
    "email": "user@example.com"
  }
}
```

### `POST /api/auth/login`
Login and return JWT token.

Request:
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

### `GET /api/auth/me`
Get current user.

Headers:
`Authorization: Bearer <jwt>`

---

## Startup Workflow

### `POST /api/workflow/run`
Submit startup idea and create async workflow job.

Headers:
`Authorization: Bearer <jwt>`

Request:
```json
{
  "startup_idea": "AI platform for ..."
}
```

Response:
```json
{
  "job_id": "job_xxx",
  "status": "queued"
}
```

### `GET /api/workflow/jobs`
List all jobs for current user.

Headers:
`Authorization: Bearer <jwt>`

### `GET /api/workflow/jobs/{job_id}`
Get single job status + final result payload.

Headers:
`Authorization: Bearer <jwt>`

Result (when completed):
```json
{
  "id": "job_xxx",
  "status": "completed",
  "startup_idea": "AI platform for ...",
  "result": {
    "startup_analysis": "...",
    "market_insights": "...",
    "action_plan": ["...", "..."],
    "generated_website_files": ["index.html", "styles.css", "script.js"],
    "generated_website_repo": "https://github.com/...",
    "github_repository_link": "https://github.com/...",
    "vercel_deployment_link": "https://....vercel.app",
    "workflow_raw": {}
  }
}
```

---

## Health

### `GET /api/health`
Simple service status check.
