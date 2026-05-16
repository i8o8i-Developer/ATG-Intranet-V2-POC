# CELL — Contextual Execution & Labour Ledger

Agent 2 in the NERVE multi-agent pipeline.  
Turns meeting insights from IRIS into assigned, tracked, and bounty-rewarded tasks.

---

## Architecture summary

```
IRIS (Agent 1)
    │ NERVE event (iris.extraction.complete)
    ▼
CELL (this service, port 8002)
    ├── Extract tasks from insights.yaml (rule-based + LLM enrichment)
    ├── Deduplicate against Postgres + pgvector embeddings
    ├── Stage for PM approval (pending_pm_approval)
    ├── 8AM: Send intern todo DMs + PM digest via Slack
    ├── 11:30PM: Send EOD reminder DMs
    ├── 2AM: Parse EOD replies, flag no-shows, run escalation ladder
    └── Write approved tasks to ERP API
Agent 3 (PM Agent)
    │ POST /cell/ingest-tasks
    ▼
    Same pipeline (dedup → stage → PM approval)
```

---

## Design decisions

| Question | Decision | Rationale |
|---|---|---|
| Dedup method | pgvector cosine similarity, threshold 0.92 | Embeddings on short task titles are cheaper (~$0.00002/1K tokens) and more reliable than LLM binary classifier per pair |
| Embedding model | `text-embedding-3-small` (1536-dim) | Best cost/accuracy tradeoff for short strings |
| Scheduler | APScheduler AsyncIOScheduler | 3 fixed-time daily jobs — no distributed workers needed; Celery adds Redis/MQ overhead without benefit |
| Slack library | `slack-sdk` (official AsyncWebClient) | Official, well-maintained, async-native |
| LLM call strategy | Single GPT-4o-mini call per task (title + hours + priority) | Atomic, cheap, same latency as extraction |
| ERP write failures | Postgres `erp_write_queue` with exponential backoff (3 retries), then dead-letter + PM notified | Durable, no external queue dependency |

---

## Setup

### 1. Dependencies

```bash
pip install -r requirements.txt
```

### 2. Postgres with pgvector

```bash
# Install pgvector extension, then:
psql -d cell_db -f migrations/001_initial_schema.sql
```

### 3. Environment

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY, DATABASE_URL, R2 credentials, SLACK_BOT_TOKEN
# Set MOCK_MODE=true for local development (no real credentials needed)
```

---

## Running locally (mock mode)

Open three terminals:

**Terminal 1 — Mock ERP (port 8003)**
```bash
python -m cell.mocks.erp_server
```

**Terminal 2 — Mock Slack (port 8004)**
```bash
python -m cell.mocks.slack_server
```

**Terminal 3 — CELL**
```bash
MOCK_MODE=true uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

---

## Simulating the full daily cycle

**Step 1 — Seed tasks (simulates Agent 3 weekly push)**
```bash
python scripts/seed_agent3_tasks.py
```

**Step 2 — Simulate NERVE event from IRIS (uses standup insights)**
```bash
python scripts/seed_nerve_event.py --meeting-type standup
# or: sales, hr
# or: --flagged (simulates low-confidence IRIS extraction)
```

**Step 3 — Check staged tasks**
```bash
curl http://localhost:8002/cell/tasks/PROJ-CRM-0014
```

**Step 4 — Inject intern EOD replies into mock Slack**
```bash
curl -X POST http://localhost:8004/test/inject-message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "p-arjun-001", "text": "done 1\nblocked 2 waiting for credentials\ncarry 3"}'
```

**Step 5 — Trigger night processing manually (normally runs at 2AM IST)**
```bash
curl -X POST http://localhost:8002/cell/debug/run-night-job
```

---

## Running tests

```bash
pytest tests/ -v
```

Tests do not require live DB, Slack, or OpenAI — all external calls are mocked.

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/cell/health` | Health check |
| `POST` | `/cell/ingest-nerve` | Receive NERVE event from IRIS |
| `POST` | `/cell/ingest-tasks` | Receive Agent 3 weekly task push |
| `GET` | `/cell/tasks/{project_id}` | List staged tasks (admin/debug) |
| `POST` | `/cell/slack/events` | Slack Events API webhook (optional) |

---

## Required Slack bot scopes

```
chat:write
im:history
im:write
users:read
```

---

## Project structure

```
CELL/
├── main.py                         FastAPI entrypoint (port 8002)
├── requirements.txt
├── .env.example
├── migrations/
│   └── 001_initial_schema.sql      Postgres schema + pgvector
├── cell/
│   ├── config.py                   All settings via pydantic-settings
│   ├── api/
│   │   ├── routes.py               POST /cell/ingest-nerve, /cell/ingest-tasks, GET /cell/health
│   │   ├── pm_webhook.py           Slack Events API handler
│   │   └── pm_approval.py          PM approval processor (approve/reject/bounty)
│   ├── core/
│   │   ├── models.py               All Pydantic models
│   │   ├── extractor.py            YAML → RawTask (rule-based + LLM enrichment)
│   │   ├── deduplicator.py         pgvector cosine similarity dedup
│   │   ├── bounty.py               Bounty calculation
│   │   └── accountability.py       No-show logic + escalation ladder
│   ├── scheduler/
│   │   ├── jobs.py                 APScheduler (8AM, 11:30PM, 2AM IST)
│   │   └── clock.py                IST time helpers + day window logic
│   ├── slack/
│   │   ├── sender.py               DM delivery via slack-sdk
│   │   ├── reader.py               24hr DM history pull at 2AM
│   │   └── parser.py               EOD + PM reply parser + injection defense
│   ├── erp/
│   │   └── client.py               ERP API CRUD + retry queue processor
│   ├── storage/
│   │   └── r2_client.py            Cloudflare R2 (insights.yaml fetch)
│   ├── db/
│   │   └── postgres.py             asyncpg queries (all SQL explicit)
│   └── mocks/
│       ├── erp_server.py           Mock ERP API (port 8003)
│       ├── slack_server.py         Mock Slack API (port 8004)
│       └── nerve_sender.py         Mock NERVE event emitter
├── scripts/
│   ├── seed_nerve_event.py         Simulate IRIS → NERVE → CELL
│   └── seed_agent3_tasks.py        Simulate Agent 3 weekly push
└── tests/
    ├── conftest.py
    ├── test_extractor.py           YAML → task extraction (all meeting types)
    ├── test_deduplicator.py        Cosine sim + token overlap dedup logic
    ├── test_parser.py              EOD parser + prompt injection defense
    ├── test_bounty.py              Bounty calculation
    └── test_scheduler.py           IST clock helpers + day window logic
```

---

## What CELL does NOT do

- Does not read Slack channels — DMs only
- Does not engage in freeform conversation
- Does not set final bounty values without PM approval
- Does not close tasks without PM approval
- Does not access meeting video or raw transcripts
- Does not handle payroll or actual money transfer
