# CELL — Technical Documentation

**Full name:** Contextual Execution & Labour Ledger  
**Role in pipeline:** Agent 2 — turns meeting insights into tasks, manages intern todo delivery, bounties, and EOD accountability  
**Port:** 8002  
**Language:** Python 3.11+ / FastAPI / asyncpg / APScheduler / slack-sdk

---

## What CELL does

CELL sits between IRIS (meeting intelligence) and the human workforce. It:

1. **Receives** `iris.extraction.complete` events from IRIS via NERVE
2. **Extracts** RawTasks from `insights.yaml` using rule-based logic per meeting type
3. **Enriches** tasks via LLM (title normalisation, hour estimates, priority suggestion)
4. **Deduplicates** against Postgres using pgvector cosine similarity (threshold 0.92)
5. **Stages** new tasks in Postgres as `pending_pm_approval`
6. **8AM daily** — DMs each intern their task list; DMs each PM a digest of pending approvals
7. **11:30PM daily** — DMs every intern an EOD reminder
8. **2AM daily** — Reads DM histories, parses EOD replies, updates task statuses, flags no-shows, escalates, retries ERP writes
9. **PM approval** — On PM Slack reply, writes approved tasks to ERP API and credits bounties

---

## Architecture

```
IRIS (Agent 1)
    │ POST /cell/ingest-nerve (via NERVE)
    ▼
CELL (port 8002)
    ├── Extract tasks from insights.yaml  (rule-based, no LLM hallucination)
    ├── LLM enrich  (title + hours + priority only)
    ├── pgvector dedup  (cosine sim >= 0.92 = skip)
    ├── Stage → pending_pm_approval in Postgres
    │
    ├── 8AM  → intern todo DMs + PM digest DMs
    ├── 11:30PM → EOD reminder DMs
    ├── 2AM  → parse EODs, flag no-shows, escalate, retry ERP queue
    │
    └── PM Slack reply → approve/reject → ERP write + bounty credit

Agent 3 (PM Agent)
    │ POST /cell/ingest-tasks
    ▼ Same dedup → stage → PM approval pipeline
```

---

## API Endpoints

### `POST /cell/ingest-nerve`

Receive a NERVE event from IRIS. Returns `202 Accepted` immediately; processing runs in a background task.

**Request body:**
```json
{
  "event": "iris.extraction.complete",
  "meeting_id": "abc-defg-hij",
  "project_id": "PROJ-CRM-0014",
  "confidence_score": 0.91,
  "flagged": false,
  "insights_path": "/projects/PROJ-CRM-0014/2025-05-06_abc-defg-hij/insights.yaml",
  "timestamp": "2025-05-06T14:32:11Z"
}
```

**Response `202`:**
```json
{ "status": "accepted", "meeting_id": "abc-defg-hij" }
```

If `flagged: true`, tasks are still processed but each receives a `[LOW CONFIDENCE X%] Review before approving.` PM note.

---

### `POST /cell/ingest-tasks`

Accept a weekly task push from Agent 3 (PM Agent). Same dedup + staging pipeline. Returns `202`.

**Request body:**
```json
{
  "source": "agent3",
  "project_id": "PROJ-CRM-0014",
  "week_ref": "2025-W20",
  "tasks": [
    {
      "title": "Implement login screen",
      "assignee_id": "p-arjun-001",
      "estimated_hours": 8,
      "priority": "high",
      "due_date": "2025-05-16",
      "notes": "Use design-system v2 components"
    }
  ]
}
```

**`priority` values:** `urgent` | `high` | `normal` | `low`

---

### `GET /cell/health`

```json
{ "status": "ok", "agent": "CELL" }
```

---

### `GET /cell/tasks/{project_id}`

List all tasks with `status = pending_pm_approval` for a project. Admin/debug use.

```json
{
  "project_id": "PROJ-CRM-0014",
  "pending_tasks": [...],
  "count": 3
}
```

---

### `POST /cell/slack/events`

Slack Events API webhook. Receives PM approval replies and EOD submissions (optional — CELL also polls DM history at 2AM as the primary mechanism).

---

## Daily Scheduled Jobs (IST)

| Time | Job | What it does |
|---|---|---|
| 08:00 | `morning_job` | DMs each intern their task list for the day; DMs each PM a digest of pending approvals + flags |
| 23:30 | `eod_reminder_job` | DMs all interns with open tasks an EOD reminder |
| 02:00 | `night_process_job` | Reads DM histories, parses EOD replies, updates statuses, escalates no-shows, retries ERP queue, checks 48hr PM approval escalations |

All jobs use IST (`Asia/Kolkata`). Scheduler is APScheduler `AsyncIOScheduler`.

---

## Slack Message Formats

### Intern daily todo DM (8AM)
```
Good morning! Here are your tasks for today — 14 May 2026.

[HIGH  ] Implement login screen — due 16 May
         Est. 8hrs | Bounty: 2.5 bounties
         Reply: done 1 / blocked 1 <reason> / carry 1

Reply in this format at EOD. One line per task.
```

### EOD reminder DM (11:30PM)
```
EOD check-in reminder — please reply before 2AM.

Format for each task:
  done <task_number>
  blocked <task_number> <reason>
  carry <task_number>

Your open tasks today:
  1. Implement login screen
```

### PM morning digest DM (8AM)
```
Good morning Ananya — 14 May 2026 summary for PROJ-CRM-0014.

━━ PENDING YOUR APPROVAL ━━
3 new task(s) generated:
  1. [HIGH  ]  Implement login screen — p-arjun-001 — Est. 8hrs — 2.5 bounties
  2. [NORMAL]  Write unit tests — p-ritu-002 — Est. 4hrs — 1 bounty
  3. [HIGH  ]  Update API docs — p-arjun-001 — Est. 3hrs — 0.75 bounties

Reply: approve all / approve 1,3 / reject 2 - <reason>
You can also edit hours: approve 1 hours=6

━━ YESTERDAY'S COMPLETIONS ━━
2 task(s) marked done by interns:
  ✓ p-arjun-001 — Fix auth bug

━━ FLAGS ━━
  ⚠ p-ritu-002: WARNING: You did not submit your EOD report yesterday.
```

### PM approval reply formats
```
approve all
approve 1,3
approve 1 hours=6
reject 2 - wrong assignee
```

### Intern EOD reply formats
```
done 1
blocked 2 waiting for credentials from vendor
carry 3
```

---

## Bounty System

Bounty is a **unit count** — not INR. The accountant multiplies total units by ₹100.

**Formula:** `bounty = (estimated_hours / 4) × multiplier` — rounded to nearest 0.25.

| Priority | Multiplier | Example (8hrs) |
|---|---|---|
| `urgent` | 1.5× | 3 bounties |
| `high` | 1.25× | 2.5 bounties |
| `normal` | 1.0× | 2 bounties |
| `low` | 0.75× | 1.5 bounties |

Bounty is calculated at staging time. PM can edit `estimated_hours` at approval time, which recalculates bounty.

---

## Deduplication

- Uses `text-embedding-3-small` (1536-dim) via OpenAI
- Cosine similarity threshold: **0.92** — above this = duplicate, skip creation, update `due_date` if changed
- Secondary: token overlap threshold 0.80
- Embeddings stored in Postgres as `VECTOR(1536)` column with pgvector

---

## Accountability & Escalation

| Consecutive misses | Action |
|---|---|
| 1–2 | Warning message in next morning DM |
| 3 | Escalate to APM (Slack DM to APM) |
| 5+ | Escalate to Dept Head (Slack DM to Dept Head) |

**PM approval escalation:** If a PM digest is not responded to within 48 hours, CELL DMs the PM's Dept Head.

---

## Security — Prompt Injection Defense

CELL treats all intern Slack messages as **data tokens only**, never as instructions. The EOD parser:
- Whitelists only `done <n>`, `blocked <n> <reason>`, `carry <n>`
- Runs regex-based injection detection on every message and line
- On injection detection: returns `security_flag: true`, notifies PM via DM, does not process the message

Detected patterns include: `ignore previous instructions`, `act as`, `system:`, `jailbreak`, etc.

---

## Database Schema (Postgres + pgvector)

| Table | Purpose |
|---|---|
| `employees` | Intern/PM/APM/DeptHead registry with `slack_user_id` |
| `projects` | Project registry |
| `project_members` | Maps employees to projects with role (`intern`, `pm`) |
| `tasks` | Core task state machine with `title_embedding VECTOR(1536)` |
| `bounty_ledger` | Bounty records per task+intern |
| `eod_submissions` | Daily EOD submissions per intern+task |
| `accountability_log` | Consecutive miss tracking per intern |
| `erp_write_queue` | Durable retry queue for ERP API writes |
| `pm_approval_digests` | Tracks sent digests for 48hr escalation |

Run migration: `psql -d cell_db -f migrations/001_initial_schema.sql`

---

## ERP API Contract (what CELL calls)

CELL writes tasks to the ERP via:

```
POST <ERP_BASE_URL>/api/tasks
X-API-Key: <ERP_API_KEY>
Content-Type: application/json

{
  "title": "Implement login screen",
  "project_id": "PROJ-CRM-0014",
  "assignee_id": "p-arjun-001",
  "priority": "high",
  "due_date": "2025-05-16",
  "estimated_hours": 8.0,
  "bounty_value": 2.5,
  "status": "open",
  "source_meeting_id": "abc-defg-hij",
  "notes": null,
  "subtasks": []
}
```

**Expected response:**
```json
{
  "erp_task_id": "ERP-0042",
  "title": "...",
  "project_id": "...",
  "assignee_id": "...",
  "status": "open",
  "created_at": "2025-05-14T08:00:00Z"
}
```

**On failure:** CELL enqueues to `erp_write_queue` with exponential backoff (3 retries, base 2s). After 3 failures → `dead_letter` + PM is notified.

CELL also calls:
```
PATCH <ERP_BASE_URL>/api/tasks/<erp_task_id>   { "status": "...", "notes": "..." }
GET  <ERP_BASE_URL>/api/tasks?project_id=...&assignee_id=...&status=open
```

---

## Production Readiness Assessment

### What is ready
- Full async FastAPI service with background task processing
- Postgres + pgvector for task state and semantic dedup
- APScheduler for 3 daily jobs (IST-anchored)
- Slack DM-only delivery (no channel access)
- EOD parser with whitelist + prompt injection defense
- PM approval parser (approve/reject/bulk/hours-edit)
- Accountability tracking with APM + Dept Head escalation ladder
- ERP retry queue with dead-letter and exponential backoff (tenacity)
- PM approval 48hr escalation to Dept Head
- Full test suite (mocked — no live DB/Slack/OpenAI needed for `pytest tests/ -v`)
- Mock ERP (port 8003) and mock Slack (port 8004) for local dev
- `MOCK_MODE=true` flag for complete local simulation

### Gaps before production deploy

| # | Issue | Severity | Fix needed |
|---|---|---|---|
| 1 | **`employees` table must be seeded** | Critical | CELL reads `employees` for intern list, slack IDs, escalation chain. This table must be populated from your HR/ERP system before CELL can function. Wire a sync job. |
| 2 | **`project_members` must be seeded** | Critical | CELL looks up PMs per project from `project_members`. Populate this from ERP. |
| 3 | **Cloudflare R2 credentials missing** | Critical | CELL fetches `insights.yaml` from R2. Set `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` in prod. The `r2_client.py` uses boto3 — should work with real credentials. |
| 4 | **Slack `slack_user_id` not in employees table** | Critical | Interns are identified by `employee_id` (e.g. `p-arjun-001`). You must populate `slack_user_id` in the `employees` table. Map via Slack `users.list` API. |
| 5 | **`on_event("startup"/"shutdown")` deprecated** | Medium | FastAPI deprecated `@app.on_event`. Replace with `lifespan` context manager. |
| 6 | **`MOCK_MODE=false` switches to real Slack/ERP** | Medium | Verify real Slack bot token has scopes: `chat:write`, `im:history`, `im:write`, `users:read`. |
| 7 | **No authentication on `/cell/ingest-nerve`** | High | Add `X-API-Key` check. Only NERVE/IRIS should be able to call this. |
| 8 | **No authentication on `/cell/ingest-tasks`** | High | Add `X-API-Key` check. Only Agent 3 should call this. |
| 9 | **`pm_approval_digests.responded` never set to `TRUE`** | Medium | The PM webhook (`pm_webhook.py`) must call `UPDATE pm_approval_digests SET responded=TRUE` after a PM reply is processed, or the 48hr escalation will fire even after PM responds. |
| 10 | **SQLAlchemy imported but not used** | Low | `requirements.txt` includes `sqlalchemy[asyncio]` and `alembic`, but the code uses `asyncpg` directly. Remove or migrate to Alembic for schema versioning. |

---

## Environment Variables (production)

```env
# OpenAI (embeddings + enrichment LLM)
OPENAI_API_KEY=sk-...

# Postgres with pgvector
DATABASE_URL=postgresql+asyncpg://cell_user:cell_pass@<host>:5432/cell_db

# Cloudflare R2
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=erp-agents

# Slack
SLACK_BOT_TOKEN=xoxb-...

# ERP
ERP_BASE_URL=https://erp.internal
ERP_API_KEY=...

# CELL service
CELL_HOST=0.0.0.0
CELL_PORT=8002

# Disable mock in production
MOCK_MODE=false

# Timezone
TZ=Asia/Kolkata
```

---

## BE Integration — What the backend needs to provide/call

### 1. CELL receives from IRIS (via NERVE)

This is automatic once IRIS's `NERVE_WEBHOOK_URL` points to `https://cell.internal/cell/ingest-nerve`. No BE action needed for this path.

### 2. ERP must implement these endpoints

CELL writes tasks to ERP. Your ERP backend must expose:

```
POST   /api/tasks           Create task → return { erp_task_id, ... }
PATCH  /api/tasks/:id       Update status/notes
GET    /api/tasks            List tasks by project_id + assignee_id + status
```

Header: `X-API-Key: <ERP_API_KEY>`

### 3. Employee data sync (critical)

Populate the `employees` and `project_members` tables from your ERP/HR system:

```sql
-- employees: one row per person
INSERT INTO employees (employee_id, slack_user_id, name, role, active, department, apm_id, dept_head_id)
VALUES ('p-arjun-001', 'U01ABC123', 'Arjun Sharma', 'intern', true, 'Engineering', 'p-apm-001', 'p-head-001');

-- project_members: link PM and interns to each project
INSERT INTO project_members (project_id, employee_id, role) VALUES ('PROJ-CRM-0014', 'p-ananya-001', 'pm');
INSERT INTO project_members (project_id, employee_id, role) VALUES ('PROJ-CRM-0014', 'p-arjun-001', 'intern');
```

Run this sync on every HR change. Keep `active=false` for offboarded employees (CELL will skip them).

### 4. Agent 3 integration

When Agent 3 (PM Agent) generates a weekly task breakdown, it should call:

```
POST https://cell.internal/cell/ingest-tasks
X-API-Key: <CELL_API_KEY>
Content-Type: application/json

{
  "source": "agent3",
  "project_id": "PROJ-CRM-0014",
  "week_ref": "2025-W20",
  "tasks": [ ... ]
}
```

### 5. PM Slack setup

- Create a Slack app with scopes: `chat:write`, `im:history`, `im:write`, `users:read`
- Install in your workspace, copy `SLACK_BOT_TOKEN`
- Optionally configure Slack Events API URL as `https://cell.internal/cell/slack/events` for real-time PM reply processing (otherwise CELL reads DM history at 2AM)

### 6. Debug endpoints

During integration, use these to inspect state:

```bash
# Check what tasks are staged for PM approval
curl https://cell.internal/cell/tasks/PROJ-CRM-0014

# Manually trigger the night processing job (no need to wait for 2AM)
curl -X POST https://cell.internal/cell/debug/run-night-job
```
