# 🤖 AI Investor Intelligence Agent

> **Hackathon Submission — AI for the Indian Investor**
> An autonomous, multi-agent financial intelligence platform for Indian retail investors. Monitors ET Markets + NSE in real-time, detects alpha signals, analyzes chart patterns, provides portfolio-aware AI chat, and auto-generates market update videos — zero human editing required.

---

## 🌟 Features

| Feature | Description |
|---|---|
| **Opportunity Radar** | Continuously monitors ET Markets RSS, NSE bulk/block deals, FII/DII flows, insider trades, SEBI regulatory alerts — surfaces alpha signals as daily alerts, not summaries |
| **Chart Pattern Intelligence** | Real-time RSI, SMA crossovers (Golden/Death Cross), breakouts, support/resistance, divergences across 83-stock NSE universe with back-tested success rates |
| **Market ChatGPT** | 11-agent LangGraph pipeline — multi-step analysis, portfolio-aware answers, source-cited responses from ChromaDB RAG + Neo4j Knowledge Graph |
| **AI Market Video Engine** | Auto-generates 30–90s MP4: title card → FII/DII bar chart → NSE race chart → sector rotation pie → IPO tracker. Zero manual editing |
| **Live Intelligence Panel** | Real-time WebSocket alerts from the 5-minute autonomous scheduler |
| **Portfolio Analysis** | Sector exposure, concentration risk detection, signal cross-referencing against user holdings |

---

## 🏗️ Architecture

```
Frontend (Next.js 16 + Tailwind v4)
    ↕  REST + WebSocket
Backend (FastAPI + Python 3.14)
    ↕
LangGraph 11-Node Pipeline:
  DataIngestion → SignalDetection → TechnicalAnalysis → ContextEnrichment
  → PortfolioAnalysis → SignalScoring → [Backtesting ‖ ImpactEval]
  → Recommendation → Explanation → UserFeedback

Data Layer:
  ├── yfinance       – Live NSE/BSE OHLCV + price data (no API key needed)
  ├── ET Markets RSS – Live headlines, alpha keyword scoring
  ├── NSE Public API – FII/DII flows, bulk/block deals
  ├── Alpha Vantage  – Earnings, insider trading
  ├── ChromaDB       – Vector RAG for news + filings
  ├── Neo4j          – Knowledge graph (directors, investors, companies)
  └── Redis          – Caching, state management
```

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- **Python 3.11+** (tested on 3.14)
- **Node.js 18+**
- **Git**

### Step 1 — Clone & Open
```bash
git clone <your-repo-url>
cd ai-investor-agent
```

### Step 2 — Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create the environment file
copy .env.example .env        # Windows
# cp .env.example .env         # Mac/Linux
```

### Step 3 — Configure API Keys (`.env`)
Open `backend/.env` and set your keys:

```env
# REQUIRED — Change this for security
SECRET_KEY=your_long_random_secret_key_here

# OPTIONAL — Get free key at https://www.alphavantage.co/support/#api-key
# Without it: uses mock earnings data. yfinance works without any key.
ALPHAVANTAGE_API_KEY=demo

# OPTIONAL — only needed if you run Redis locally
REDIS_URL=redis://localhost:6379

# OPTIONAL — only needed if you run Neo4j locally
NEO4J_URI=bolt://localhost:7687

# OPTIONAL — only needed if you run ChromaDB locally
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

> **Without Redis/Neo4j/ChromaDB:** The system runs fully with in-memory fallbacks. You only miss persistent caching and knowledge graph queries.

### Step 4 — Start the Backend
```bash
# Run from the project ROOT (not inside /backend)
cd ..
python -m uvicorn backend.main:app --reload --port 8000
```

✅ Backend is ready at `http://localhost:8000`
📖 API docs at `http://localhost:8000/docs`

### Step 5 — Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

✅ Frontend is ready at `http://localhost:3000`

---

## 🔑 API Keys Reference

| Key | Required? | Free? | Get it from |
|---|---|---|---|
| `ALPHAVANTAGE_API_KEY` | Optional | ✅ Free | [alphavantage.co](https://www.alphavantage.co/support/#api-key) — 30 seconds |
| `SECRET_KEY` | Yes (for auth) | N/A | Set any long random string |
| `REDIS_URL` | Optional | ✅ Free | `docker run -p 6379:6379 redis` |
| `NEO4J_URI` | Optional | ✅ Free tier | [neo4j.com/aura](https://neo4j.com/cloud/platform/aura-graph-database/) |
| `CHROMA_HOST` | Optional | ✅ Free | `pip install chromadb && chroma run --port 8001` |

**yfinance** (live NSE/BSE charts) and **ET Markets RSS** (live headlines) work with no API key at all.

---

## 🟢 What's Running Right Now vs What Needs Starting

### Always Running (after Quick Start steps above)
| Service | URL | How it starts |
|---|---|---|
| **Frontend Dashboard** | http://localhost:3000 | `npm run dev` |
| **Backend API** | http://localhost:8000 | `python -m uvicorn backend.main:app --reload --port 8000` |
| **API Swagger Docs** | http://localhost:8000/docs | auto (part of FastAPI) |

### Optional Services (NOT required — app auto-falls-back without them)

These services enhance the platform but the system runs perfectly without them:

#### Redis (API caching — 10min TTL)
Without it: uses a Python dict in-memory (cache lost on restart).
```bash
# Option A: Docker (recommended)
docker run -d -p 6379:6379 --name redis redis:alpine

# Option B: Windows installer
# Download from https://github.com/microsoftarchive/redis/releases
```

#### ChromaDB (Vector RAG for news/filings)
Without it: uses in-memory keyword search (fast, works fine for demo).
```bash
# Option A: pip
pip install chromadb
chroma run --host localhost --port 8001

# Option B: Docker
docker run -d -p 8001:8000 chromadb/chroma
```
> Access at: http://localhost:8001

#### Neo4j (Knowledge Graph — company relationships)
Without it: graph queries return empty objects (system still works fully).
```bash
# Option A: Docker
docker run -d -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/testpassword \
  neo4j:latest

# Option B: Free cloud (no install needed)
# https://neo4j.com/cloud/platform/aura-graph-database/
```
> Browser at: http://localhost:7474 | Username: `neo4j` | Password: `testpassword`

---

## 🐳 Full Stack with Docker Compose (Run Everything Together)

Starts all services (backend, frontend, Redis, Neo4j, ChromaDB) in one command:

```bash
docker-compose up --build
```

| Service | URL | Notes |
|---|---|---|
| Frontend | http://localhost:3000 | Dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Neo4j Browser | http://localhost:7474 | Only with Docker Compose |
| ChromaDB | http://localhost:8001 | Only with Docker Compose |

---

## 🗂️ Project Structure

```
ai-investor-agent/
├── backend/
│   ├── agents/           # LangGraph nodes (graph.py, nodes.py, state.py)
│   ├── analysis/         # Technical analysis, portfolio, scoring, backtesting
│   ├── api/
│   │   ├── routes/       # REST endpoints: chat, radar, market, portfolio, video, auth
│   │   └── websockets/   # Live Intelligence WebSocket server
│   ├── core/             # Config (settings, .env), security (JWT + hashlib)
│   ├── data/             # nse_liquid_universe.json (83 NSE stocks)
│   ├── data_pipeline/    # yfinance, Alpha Vantage, ET Markets RSS, NSE client
│   ├── scheduler/        # APScheduler: radar 5m, pipeline 7m, NSE scan 25m
│   ├── services/         # Opportunity radar, video engine, ChromaDB, Neo4j, cache
│   ├── static/
│   │   └── generated_videos/  # Auto-generated MP4/GIF market wraps
│   ├── main.py           # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/          # Next.js app router, globals.css
│       ├── components/   # AlertPanel, ChatInterface, StockChart, SignalInsights,
│       │                 #   MarketVideoPanel, PortfolioDashboard, LoginBar
│       └── lib/          # api.ts (authHeaders, getToken, login)
├── .env.example          # Template environment file
├── docker-compose.yml
└── README.md
```

---

## 🧪 Verify Everything is Working

After starting both servers, test these endpoints in your browser or terminal:

```bash
# Health check
curl http://localhost:8000/health
# → {"status":"ok","environment":"development"}

# Live opportunity radar (no login needed)
curl http://localhost:8000/api/v1/radar/opportunities
# → {"signals":[...50 live ET Markets + NSE signals...]}

# Live NSE OHLCV chart data (no login needed)
curl "http://localhost:8000/api/v1/market/ohlcv?symbol=RELIANCE.NS&period=3mo"
# → {"symbol":"RELIANCE.NS","series":[...62 OHLCV rows...]}

# Market ChatGPT (no login needed)
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Should I buy Reliance?"}'
# → {"reply":"...11-agent analysis...","sources":["ET Markets RSS","ChromaDB RAG",...]}
```

---

## 🔐 Default Login

The app works **without login** for all core features (charts, radar, chatbot, video).
To log in and see portfolio-aware features:

| Field | Value |
|---|---|
| Username | `testuser` |
| Password | `password123` |

---

## 🚨 Troubleshooting

### `ModuleNotFoundError: No module named 'backend'`
Run uvicorn from the **project root** (`ai-investor-agent/`), not from inside `backend/`:
```bash
# ✅ Correct
python -m uvicorn backend.main:app --reload --port 8000

# ❌ Wrong
cd backend && uvicorn main:app
```

### Port 8000 is busy / CORS errors
If another process is using port 8000, use a different port:
```bash
python -m uvicorn backend.main:app --reload --port 8001
```
Then update `frontend/src/lib/api.ts` — change `localhost:8000` to `localhost:8001`.

### `bcrypt`/`passlib` errors on Python 3.14
These libraries were removed. The app uses `hashlib.sha256` for password hashing. If you see these errors, delete `__pycache__` folders and restart:
```bash
# Windows PowerShell
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```

### AI Market Video fails on first click
First generation takes **60–90 seconds** because it downloads 83 NSE stock histories from yfinance. The button shows live steps (Scanning NSE universe → Building FII/DII → Rendering race chart → Encoding). Second click is fast (patterns cached for 2 hours).

### Live Intelligence panel is blank
The panel pre-loads from the REST radar feed. If it's still blank, check that:
1. The backend is running at port 8000
2. The WebSocket connects at `ws://localhost:8000/ws/alerts/`

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, Tailwind CSS v4, Recharts, Lucide, react-use-websocket |
| Backend | FastAPI, Uvicorn, Pydantic v2, Python 3.14 |
| Orchestration | LangGraph, LangChain |
| Scheduling | APScheduler (radar 5m, pipeline 7m, NSE scan 25m) |
| Data | yfinance, Alpha Vantage, ET Markets RSS, NSE India public API |
| Vector DB | ChromaDB (in-memory fallback if offline) |
| Knowledge Graph | Neo4j (empty fallback if offline) |
| Cache | Redis (dict fallback if offline) |
| Security | python-jose JWT, hashlib SHA-256 |
| Video | matplotlib, imageio, imageio-ffmpeg (GIF fallback) |

---

## 📄 License

MIT
