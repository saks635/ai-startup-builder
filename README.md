# 🚀 AI Startup Builder

An AI-powered platform that takes your startup idea and automatically generates **business analysis**, **market research**, a **multi-page website**, pushes it to **GitHub**, and deploys it live on **Vercel** — all in one click.

---

## ⚡ How It Works

```
You describe your startup idea
        ↓
   3 AI Agents run in sequence
        ↓
┌──────────────────────────────────┐
│  Agent 1: Idea Analyzer          │  → Structured business analysis
│  (Groq / LLaMA 3.3 70B)         │     (problem, solution, UVP, risks)
├──────────────────────────────────┤
│  Agent 2: Market Researcher      │  → Competitors, demand, trends
│  (Groq / LLaMA 3.3 70B)         │     (uses Tavily web search)
│  + Tavily Search Tool            │
├──────────────────────────────────┤
│  Agent 3: Website Generator      │  → Multi-page startup website
│  (Google Gemini 2.5 Flash)       │     (index, about, pricing, contact)
└──────────────────────────────────┘
        ↓
   GitHub Repo Created (user's account)
        ↓
   Vercel Deployment (live URL)
        ↓
   Results displayed in dashboard
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Framework** | [CrewAI](https://crewai.com) — multi-agent orchestration |
| **LLMs** | Groq (LLaMA 3.3 70B) for analysis & research, Google Gemini 2.5 Flash for website generation |
| **Web Search** | [Tavily API](https://tavily.com) — real-time market research |
| **Backend** | Python, FastAPI, Uvicorn |
| **Auth** | JWT (HMAC-SHA256), PBKDF2 password hashing |
| **Database** | MongoDB |
| **Job Queue** | Redis |
| **Deployment** | GitHub API (repo creation), Vercel API (deployment) |
| **Frontend** | HTML5, Bootstrap 5, Vanilla JS |
| **Containerization** | Docker Compose (MongoDB + Redis) |

---

## 📁 Project Structure

```
ai-startup-builder/
├── backend/
│   ├── main.py                  # FastAPI app — auth, workflow, integrations
│   ├── storage.py               # MongoDB storage layer
│   ├── job_queue.py             # Redis job queue
│   ├── requirements.txt         # Python dependencies
│   ├── agents/
│   │   ├── idea_analyzer.py     # Agent 1 — startup idea analysis
│   │   ├── market_researcher.py # Agent 2 — market research + web search
│   │   ├── website_generator.py # Agent 3 — website code generation
│   │   └── tasks.py             # CrewAI task definitions
│   ├── services/
│   │   ├── github_service.py    # Create repos via GitHub API
│   │   ├── vercel_service.py    # Deploy to Vercel API
│   │   ├── github_oauth.py      # GitHub OAuth flow
│   │   └── vercel_oauth.py      # Vercel OAuth flow
│   ├── tools/
│   │   └── search_tool.py       # Tavily web search tool
│   └── workflows/
│       └── startup_workflow.py  # Main orchestration pipeline
├── frontend/
│   ├── login.html               # Login page
│   ├── signup.html              # Signup + GitHub/Vercel token entry
│   ├── dashboard.html           # Submit ideas + manage integrations
│   ├── results.html             # View analysis, links, and files
│   └── assets/
│       ├── css/app.css          # Dark theme styles
│       └── js/
│           ├── api.js           # API client (auth, workflow, integrations)
│           ├── auth.js          # Session & token management
│           ├── login.js         # Login form handler
│           ├── signup.js        # Signup + token connect handler
│           ├── dashboard.js     # Dashboard + integration panel
│           └── results.js       # Job results polling & display
├── .env                         # API keys and config (not committed)
├── .gitignore
└── docker-compose.yml           # MongoDB + Redis containers
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- MongoDB (local or Atlas)
- Redis (local or cloud)
- API keys: Groq (×2), Gemini, Tavily, GitHub PAT, Vercel Token

### 2. Clone & Setup

```bash
git clone <repo-url>
cd ai-startup-builder

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GROQ_API_KEY_AGENT1=gsk_...
GROQ_API_KEY_AGENT2=gsk_...
GEMINI_API_KEY=AIza...
TAVILY_API_KEY=tvly-...
GITHUB_TOKEN=ghp_...           # Fallback system token
VERCEL_TOKEN=vcp_...           # Fallback system token
MONGODB_URL=mongodb://localhost:27017/ai_startup_builder
REDIS_URL=redis://127.0.0.1:6379/0
```

### 4. Start Services

```bash
# Start MongoDB + Redis (via Docker)
docker-compose up -d

# Start the backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Open the App

Visit **http://localhost:8000/app/login.html** in your browser.

---

## 🔑 Key Features

- **Multi-Agent AI Pipeline** — 3 specialized AI agents collaborate to analyze, research, and build
- **Automatic GitHub Repo** — website code pushed to user's own GitHub account
- **Automatic Vercel Deploy** — live website URL generated instantly
- **User Token Integration** — connect your own GitHub/Vercel during signup or on the dashboard
- **Background Job Queue** — Redis-backed queue with polling results page
- **Dark Interactive UI** — glassmorphism cards, gradient buttons, hover glow effects
- **JWT Auth** — secure stateless authentication with 12-hour token TTL

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Create account |
| `POST` | `/api/auth/login` | Login |
| `GET` | `/api/auth/me` | Current user + integration status |
| `POST` | `/api/workflow/run` | Submit startup idea |
| `GET` | `/api/workflow/jobs` | List user's jobs |
| `GET` | `/api/workflow/jobs/:id` | Get job status & results |
| `POST` | `/api/integrations/github/connect` | Connect GitHub token |
| `POST` | `/api/integrations/vercel/connect` | Connect Vercel token |
| `POST` | `/api/integrations/github/disconnect` | Disconnect GitHub |
| `POST` | `/api/integrations/vercel/disconnect` | Disconnect Vercel |

---

## 🧠 Agent Details

| Agent | Model | Purpose | Key Config |
|-------|-------|---------|------------|
| **Idea Analyzer** | `groq/llama-3.3-70b-versatile` | Structured business analysis (problem, solution, UVP, risks, monetization) | temp: 0.3, max_tokens: 600 |
| **Market Researcher** | `groq/llama-3.3-70b-versatile` + Tavily | Web search for competitors, trends, funding signals, gaps | temp: 0.2, max_tokens: 420 |
| **Website Generator** | `gemini/gemini-2.5-flash` | Multi-page startup website (HTML/CSS/JS) | temp: 0.25, max_tokens: 1400 |

---

