-- CELL v1 Initial Schema Migration
-- Run this against a Postgres instance with the pgvector extension installed.
-- Enable pgvector first: CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────
-- pgvector extension (must be installed on the Postgres server)
-- ─────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────
-- Employees (read-only for CELL — maintained by ERP/HR)
-- Included here so tests / dev setup work standalone.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    employee_id   VARCHAR PRIMARY KEY,
    slack_user_id VARCHAR UNIQUE,
    name          VARCHAR NOT NULL,
    role          VARCHAR NOT NULL,  -- intern | apm | tech_lead | dept_head | ceo
    active        BOOLEAN DEFAULT TRUE,
    department    VARCHAR,
    apm_id        VARCHAR REFERENCES employees(employee_id),
    dept_head_id  VARCHAR REFERENCES employees(employee_id),
    created_at    TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- Projects
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    project_id  VARCHAR PRIMARY KEY,
    name        VARCHAR NOT NULL,
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_members (
    id          SERIAL PRIMARY KEY,
    project_id  VARCHAR NOT NULL REFERENCES projects(project_id),
    employee_id VARCHAR NOT NULL REFERENCES employees(employee_id),
    role        VARCHAR NOT NULL,  -- intern | pm | dept_head
    UNIQUE(project_id, employee_id)
);

-- ─────────────────────────────────────────────────────────────
-- Tasks (CELL state machine — mirrors ERP)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tasks (
    id                 SERIAL PRIMARY KEY,
    erp_task_id        VARCHAR UNIQUE,
    project_id         VARCHAR NOT NULL,
    assignee_id        VARCHAR NOT NULL,
    title              VARCHAR NOT NULL,
    title_embedding    VECTOR(1536),         -- text-embedding-3-small dimension
    priority           VARCHAR,              -- urgent | high | normal | low
    estimated_hours    FLOAT,
    due_date           DATE,
    bounty_value       FLOAT,   -- bounty units (not INR); accountant × ₹100 = payout
    status             VARCHAR NOT NULL DEFAULT 'open',
    -- open | in_progress | pending_pm_approval | pending_approval
    -- | approved | rejected | deadline_missed | blocked | closed
    source             VARCHAR NOT NULL DEFAULT 'iris',  -- iris | agent3 | manual
    source_meeting_id  VARCHAR,
    pm_notes           TEXT,
    created_at         TIMESTAMP DEFAULT NOW(),
    updated_at         TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_assignee ON tasks(project_id, assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_status ON tasks(assignee_id, status);

-- ─────────────────────────────────────────────────────────────
-- Bounty Ledger
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bounty_ledger (
    id                SERIAL PRIMARY KEY,
    task_erp_id       VARCHAR NOT NULL,
    intern_id         VARCHAR NOT NULL,
    project_id        VARCHAR NOT NULL,
    estimated_hours   FLOAT,
    priority          VARCHAR,
    bounty_value      FLOAT,   -- bounty units (not INR)
    status            VARCHAR DEFAULT 'pending',  -- pending | approved | rejected
    approved_by       VARCHAR,
    approved_at       TIMESTAMP,
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bounty_intern ON bounty_ledger(intern_id);
CREATE INDEX IF NOT EXISTS idx_bounty_status ON bounty_ledger(status);

-- ─────────────────────────────────────────────────────────────
-- EOD Submissions
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eod_submissions (
    id               SERIAL PRIMARY KEY,
    intern_id        VARCHAR NOT NULL,
    task_id          INTEGER REFERENCES tasks(id),
    submission_date  DATE NOT NULL,
    status           VARCHAR,      -- done | blocked | carry | missed
    block_reason     TEXT,
    raw_message      TEXT,
    parse_success    BOOLEAN,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eod_intern_date ON eod_submissions(intern_id, submission_date);

-- ─────────────────────────────────────────────────────────────
-- Accountability Log
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accountability_log (
    id                     SERIAL PRIMARY KEY,
    intern_id              VARCHAR NOT NULL,
    date                   DATE NOT NULL,
    eod_submitted          BOOLEAN DEFAULT FALSE,
    tasks_missed           INTEGER DEFAULT 0,
    consecutive_miss_count INTEGER DEFAULT 0,
    warning_sent           BOOLEAN DEFAULT FALSE,
    escalated_to           VARCHAR,
    created_at             TIMESTAMP DEFAULT NOW(),
    UNIQUE(intern_id, date)
);

-- ─────────────────────────────────────────────────────────────
-- ERP Write Queue (retry / dead-letter)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS erp_write_queue (
    id             SERIAL PRIMARY KEY,
    task_id        INTEGER NOT NULL REFERENCES tasks(id),
    payload        JSONB NOT NULL,
    attempt_count  INTEGER DEFAULT 0,
    last_error     TEXT,
    status         VARCHAR DEFAULT 'pending',  -- pending | success | dead_letter
    next_retry_at  TIMESTAMP DEFAULT NOW(),
    created_at     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_erp_queue_status_retry ON erp_write_queue(status, next_retry_at);

-- ─────────────────────────────────────────────────────────────
-- PM Approval Digests (track sent digests for escalation timing)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pm_approval_digests (
    id          SERIAL PRIMARY KEY,
    project_id  VARCHAR NOT NULL,
    pm_id       VARCHAR NOT NULL,
    sent_at     TIMESTAMP DEFAULT NOW(),
    responded   BOOLEAN DEFAULT FALSE,
    responded_at TIMESTAMP
);
