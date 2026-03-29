# AI Investor Intelligence Agent
## Hackathon Submission Document
### Problem: AI for the Indian Investor

---

# Part 1 — Architecture Document

## System Overview

The AI Investor Intelligence Agent is an autonomous, multi-agent financial intelligence platform built for Indian retail investors. It continuously ingests financial data streams, detects alpha-generating signals, analyzes technical patterns, provides portfolio-aware AI reasoning, and auto-generates market update videos — requiring zero human intervention between signal detection and investor alert delivery.

---

## Agent Roles & Responsibilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AI INVESTOR INTELLIGENCE AGENT                         │
│                         11-Node LangGraph Pipeline                          │
└─────────────────────────────────────────────────────────────────────────────┘

 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │  DATA         │    │  SIGNAL       │    │  TECHNICAL    │    │  CONTEXT     │
 │  INGESTION   │───▶│  DETECTION    │───▶│  ANALYSIS    │───▶│  ENRICHMENT │
 │  AGENT       │    │  AGENT        │    │  AGENT       │    │  AGENT       │
 └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                   │                    │                    │
  yfinance             ET Markets           RSI, SMA             ChromaDB
  AlphaVantage         RSS Feeds            Breakout             RAG Lookup
  NSE Client           Bulk Deals           Divergence           Neo4j Graph
  ET RSS               FII/DII              Backtesting          Filing Parser
  Redis Cache          SEBI Alerts          Golden Cross         News Scraper

         ┌──────────────────────────────────────────────────────┐
         ▼                                                       │
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
 │  PORTFOLIO   │    │  SIGNAL       │    │  BACKTEST +  │      │
 │  ANALYSIS   │───▶│  SCORING     │───▶│  IMPACT EVAL │      │
 │  AGENT       │    │  AGENT       │    │  (Parallel)  │      │
 └──────────────┘    └──────────────┘    └──────────────┘      │
       │                   │                    │                │
  Sector Exposure     0–10 Strength        2yr Forward       Feedback
  Concentration      Portfolio Bonus       Return Score      Loop ─────┘
  Risk Alerts        Volume Bonus          FII/DII Impact

         ┌───────────────────────────────────────────────────────┐
         ▼                                                        ▼
 ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────┐
 │  RECOMMEN-   │    │  EXPLANATION │    │  USER FEEDBACK / OUTPUT ROUTER   │
 │  DATION     │───▶│  AGENT       │───▶│  WebSocket Push · REST API       │
 │  AGENT       │    │  AGENT       │    │  AI Video Engine · ChatGPT       │
 └──────────────┘    └──────────────┘    └──────────────────────────────────┘
       │                   │
  Strong Buy/Sell      Plain-English +
  Hold/Review          Backtested %
  Score-Driven         Source Citations
```

---

## Detailed Agent Descriptions

### Agent 1 — Data Ingestion Agent
**Role:** Orchestrates all external data collection for every ticker being analyzed.

**Data Sources Integrated:**
| Source | Data Type | Frequency |
|---|---|---|
| `yfinance` | Live price, OHLCV 6-month history | Per request |
| Alpha Vantage | Earnings announcements, EPS estimates | Per request |
| Alpha Vantage | Insider trading transactions | Per request |
| ET Markets RSS | Live headlines (50 latest), alpha keyword scoring | Per request |
| NSE India API | FII/DII institutional flows | Per request |
| NSE India API | Bulk deals, block deals | Per request |
| ChromaDB / In-memory | News articles, corporate filings | Stored & indexed |

**Error Handling:**
- Redis cache checked first (10-min TTL) — avoids rate limiting
- Each external call wrapped in try/except — partial failures don't abort the pipeline
- Returns zeroed data structure on total failure (pipeline continues)

---

### Agent 2 — Signal Detection Agent (Opportunity Radar)
**Role:** Not a summarizer — a signal-finder. Detects alpha-generating corporate events from ET Markets headlines, NSE bulk deals, FII/DII flows, and SEBI regulatory notices.

**Alpha Keyword Taxonomy:**
```
WATCH_BUY_FLOW  →  block deal | bulk deal | insider buy | promoter buying
RISK_REVIEW     →  SEBI notice | regulatory | penalty | investigation
ALPHA_SCAN      →  3+ alpha keywords: earnings, guidance, upgrade, downgrade,
                   results, FII, DII, IPO, listing, rating change
```

**Scoring Formula:**
```
confidence = min(0.95, 0.35 + (0.2 × keyword_hits + 0.15 × title_word_count
             + 2.0 × is_bulk_deal + 1.5 × is_regulatory) / 25)
```

---

### Agent 3 — Technical Analysis Agent
**Role:** Computes 6 native technical indicators from 6-month daily OHLCV data across 83 NSE liquid stocks. No external TA library (bypasses Numba/C-extension incompatibilities).

| Pattern | Method | Confidence |
|---|---|---|
| Golden Cross | SMA-20 crosses above SMA-50 | 0.82 |
| Death Cross | SMA-20 crosses below SMA-50 | 0.82 |
| Breakout Bullish | Close > 20-day rolling high (with volume) | 0.65–0.88 |
| Breakdown Bearish | Close < 20-day rolling low (with volume) | 0.65–0.88 |
| RSI Oversold | RSI-14 < 30 | 0.75 |
| RSI Overbought | RSI-14 > 70 | 0.75 |
| Bullish Divergence | Price new low, RSI higher low, < 40 | 0.72 |
| Bearish Divergence | Price new high, RSI lower high, > 60 | 0.72 |
| Volume Spike | Volume > 2× 20-day average | 0.85 |

**NSE Universe:** 83 liquid stocks including NIFTY 50, NIFTY Next 50, and mid-caps.
**Scan cadence:** Every 25 minutes via APScheduler.

---

### Agent 4 — Context Enrichment Agent
**Role:** Provides RAG-augmented historical and news context around each signal.

**Tools Integrated:**
- **ChromaDB Vector DB** — stores and retrieves ET Markets articles, corporate filings, news by semantic similarity. Falls back to in-memory keyword search if ChromaDB offline.
- **Neo4j Knowledge Graph** — queries entity relationships: `(Person)-[:DIRECTOR_OF]->(Company)`, `(Person)-[:INVESTOR_IN]->(Company)`. Falls back to empty dict if Neo4j offline.

---

### Agent 5 — Portfolio Analysis Agent
**Role:** Cross-references all detected signals against the user's personal holdings.

**Outputs:**
- Total portfolio value
- Sector exposure breakdown (%)
- Concentration risk alert (triggers if any sector > 40% of book)
- Affected holdings: which stocks in the portfolio are directly impacted by detected signals
- Estimated P&L impact per holding (+2.4% bullish / -1.5% bearish)

---

### Agent 6 — Signal Scoring Agent
**Role:** Compound scoring of all signals on a 0–10 scale.

```
final_score = min(10.0,
    (base_confidence × 10)
    + (1.5 if volume_confirmed else 0)
    + (2.0 if portfolio_weight > 10% else 1.0 if portfolio_weight > 0 else 0)
)
```
Signals sorted descending by score before passing to recommendation.

---

### Agent 7 — Backtesting Agent *(runs in parallel with Agent 8)*
**Role:** Calculates real historical success rate for each pattern on each specific stock using 2 years of daily yfinance OHLCV.

**Method:** Forward-return analysis — "after this pattern appeared on this stock, what % of the next 5-day windows were profitable?"

```python
hits = (forward_5d_returns > 0).sum() / len(valid_returns)
success_rate = min(0.95, max(0.35, hits))
```

Falls back to pattern-family heuristics if data unavailable:
- Bullish patterns: 62% baseline
- Bearish patterns: 58% baseline
- Neutral: 52% baseline

---

### Agent 8 — Impact Evaluation Agent *(runs in parallel with Agent 7)*
**Role:** Adds macroeconomic and institutional flow context.
- Pulls live FII/DII flow from NSE India public API
- Adds portfolio concentration metrics
- Labels signals with estimated ROI category and risk score

---

### Agent 9 — Recommendation Agent
```
signal_score > 7.5  →  "Strong Buy"
signal_score > 6.0  →  "Buy"
signal_score < 4.0  →  "Sell"
otherwise           →  "Hold"
```

---

### Agent 10 — Explanation Agent
**Role:** Generates plain-English explanation combining pattern name, back-tested success rate, and contextual enrichment count.

**Example output:**
> *"RELIANCE.NS: breakout_bullish with volume confirmation — back-tested hit-rate ~74.0% on 2yr history. Enriched with 3 ChromaDB sources and Neo4j entity context. Avg success rate across 5 signals: 68.2%."*

---

## Communication Architecture

```
APScheduler (Background Threads)
    │
    ├─ Every 5 min  →  Opportunity Radar Refresh  →  WebSocket Broadcast
    ├─ Every 7 min  →  Full LangGraph Pipeline     →  WebSocket Broadcast
    └─ Every 25 min →  NSE Universe Technical Scan →  Cache Update

User Request (Chat / UI)
    │
    ▼
FastAPI REST Endpoint
    │
    ▼
LangGraph execute_agent_workflow()
    │
    ├── Node 1: DataIngestion      ─── Redis cache → yfinance / AlphaVantage / ET RSS
    ├── Node 2: SignalDetection    ─── OpportunityRadar.get_signals()
    ├── Node 3: TechnicalAnalysis  ─── TechnicalAnalyzer.analyze(ohlcv_df)
    ├── Node 4: ContextEnrichment  ─── ChromaDB.query() + Neo4j.query()
    ├── Node 5: PortfolioAnalysis  ─── PortfolioAnalyzer.analyze_portfolio()
    ├── Node 6: SignalScoring      ─── SignalScorer.score_signals()
    ├── Node 7: Backtesting    ─┐  (run
    ├── Node 8: ImpactEval     ─┘   parallel)
    ├── Node 9: Recommendation     ─── score → BUY/SELL/HOLD/STRONG BUY
    ├── Node 10: Explanation       ─── plain-English + source citations
    └── Node 11: UserFeedback      ─── WebSocket push to connected clients
    │
    ▼
JSON Response: { reply, sources[], recommendation, signal_score,
                 portfolio_impact, affected_holdings }
```

---

## Error-Handling Logic

| Failure Point | Fallback Behaviour | Impact |
|---|---|---|
| Redis unavailable | Python dict in-memory cache | Cache lost on restart, functionally equivalent |
| ChromaDB unavailable | In-memory BM25 keyword search | Slightly lower RAG quality, no data loss |
| Neo4j unavailable | Returns `{}` for graph queries | Agent skips enrichment, pipeline continues |
| yfinance rate-limited | Returns zeroed price dict | Technical analysis skipped for that ticker |
| NSE API blocked | FII/DII frame shows "data unavailable" | Impact agent uses placeholder, continues |
| Alpha Vantage `demo` key | Returns mock earnings/insider data | Earnings signals use placeholders |
| imageio MP4 fail | Auto-falls back to animated GIF | Video still generated, slightly larger file |
| LangGraph node exception | Logs error, returns safe default state | User sees partial results, not crash |
| WebSocket client disconnect | Removed from connection pool | No server error, clean disconnect |

---

# Part 2 — Impact Model

## Business Impact Quantification

### Target User
**Indian retail investor** with ₹5–25 lakh portfolio, monitoring 10–30 NSE/BSE stocks across sectors.

India has **14 crore+ active demat accounts** as of 2024 (SEBI data).
Active traders (≥1 trade/month): approximately **2.5 crore users** — the addressable base.

---

## Time Saved Per User Per Day

| Activity (Manual Today) | Time Spent (Manual) | Time With Agent | Saving |
|---|---|---|---|
| Reading ET Markets / CNBC | 45 min/day | 0 min (pushed automatically) | **45 min** |
| Scanning charts for patterns | 30 min/day | 0 min (NSE scan every 25 min) | **30 min** |
| Reading corporate filings / bulk deal notices | 20 min/day | 0 min (signal alert pushed) | **20 min** |
| Researching FII/DII data on NSE website | 15 min/day | 0 min (embedded in signal card) | **15 min** |
| Asking broker / Twitter for stock opinion | 20 min/day | 2 min (Market ChatGPT) | **18 min** |
| Calculating portfolio sector exposure | 10 min/week | 0 min (Exposure Vault live) | ~**1.5 min/day** |
| **Total** | **~142 min/day** | **~2 min/day** | **~140 min/day** |

**Assumption:** Average knowledge worker values time at ₹300/hour (₹5/min).

```
Daily time value saved per user = 140 min × ₹5/min = ₹700/day
Annual saving per user          = ₹700 × 250 trading days = ₹1,75,000/year
```

---

## Missed Opportunity Cost Recovered

**Scenario:** Retail investor typically misses 2–3 bulk deal / insider buy alerts per month that would have yielded +3–5% returns if acted on within 24 hours.

| Metric | Conservative | Moderate |
|---|---|---|
| Portfolio size | ₹5 lakh | ₹15 lakh |
| Missed alpha events/month | 2 | 3 |
| Average gain per event (if caught) | 3% | 4% |
| Capital deployed per event | ₹50,000 | ₹2,00,000 |
| Monthly recovered opportunity | ₹3,000 | ₹24,000 |
| **Annual recovered opportunity** | **₹36,000** | **₹2,88,000** |

**Assumption:** Agent catches 70% of relevant signals (30% filtered as false positives or NSE data unavailable). Net recovery = 70% of above.

```
Conservative net annual recovery = ₹36,000 × 0.70 = ₹25,200/user/year
Moderate net annual recovery     = ₹2,88,000 × 0.70 = ₹2,01,600/user/year
```

---

## Market Scale Estimate

| Metric | Value | Assumption |
|---|---|---|
| Addressable active traders | 2.5 crore | SEBI 2024 data |
| Adoption rate (Year 1) | 0.5% | Conservative SaaS benchmark |
| **Year 1 Users** | **1,25,000** | |
| Subscription price | ₹499/month | Below Zerodha Kite plan |
| **Annual Revenue (Year 1)** | **₹7.5 crore** | 1,25,000 × ₹599 × 12... ≈ ₹7.5Cr |
| Gross margin (SaaS) | 75% | Infrastructure ~25% |
| **Gross Profit (Year 1)** | **~₹5.6 crore** | |

---

## Cost Reduction for ET Markets / Financial Media

**Perspective:** If deployed as ET Markets intelligence layer product:

| Cost Item | Current Manual Cost | With Automation | Saving |
|---|---|---|---|
| Research analysts (signal curation) | ₹12–18L/analyst × 10 analysts | 1 oversight analyst | ₹1–1.5 crore/year |
| Video production (daily wrap) | ₹8,000–15,000/video × 250 days | ₹0 (automated) | ₹20–37.5 lakh/year |
| Data vendor subscriptions | ₹25–40L/year | ₹8–12L (yfinance + free feeds) | ₹15–30 lakh/year |
| **Total Annual Cost Reduction** | | | **₹1.5–2.1 crore/year** |

---

## Summary Impact Table

| Impact Category | Per User | At 1.25L Users Scale |
|---|---|---|
| Time saved | 140 min/day | 29.2 crore minutes/day |
| Time value recovered | ₹1.75L/year | ₹2,187 crore/year |
| Missed alpha recovered (conservative) | ₹25,200/year | ₹315 crore/year |
| Revenue potential (SaaS) | ₹5,988/year | ₹7.5 crore ARR (Year 1) |
| ET Markets cost reduction | N/A | ₹1.5–2.1 crore/year |

---

## Key Assumptions

1. **Time valuation:** ₹300/hour (₹5/min) — Indian urban professional average (2024)
2. **Alpha recovery rate:** 70% of surfaced signals are actionable (30% false positive rate)
3. **Signal frequency:** 2–3 meaningful corporate events per stock per month on NSE
4. **Average return per acted signal:** 3–4% over 5-day window (conservative, supported by bulk deal literature)
5. **Demat account base:** 14 crore accounts, 2.5 crore active traders (SEBI Annual Report 2023–24)
6. **Year 1 adoption:** 0.5% of active trader base — typical early-stage B2C fintech benchmark
7. **Subscription pricing:** ₹499/month — positioned below Zerodha Kite's premium features
8. **Infrastructure cost:** ~25% of revenue — includes API costs, cloud hosting, yfinance fallback, storage

---

*Document prepared for: ET Hackathon — AI for the Indian Investor*
*System: AI Investor Intelligence Agent | Stack: FastAPI · LangGraph · Next.js · yfinance · ET Markets RSS*
