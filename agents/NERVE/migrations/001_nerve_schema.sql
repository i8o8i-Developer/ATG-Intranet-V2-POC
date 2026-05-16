-- Every event NERVE receives or generates (append-only, never deleted)
CREATE TABLE nerve_event_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR NOT NULL,
    source VARCHAR,                    -- which agent/system sent it
    project_id VARCHAR,
    meeting_id VARCHAR,
    details JSONB,
    status VARCHAR DEFAULT 'received',
    error_message TEXT
);

-- Every job trigger and its result
CREATE TABLE nerve_job_log (
    id SERIAL PRIMARY KEY,
    trigger_id UUID NOT NULL DEFAULT gen_random_uuid(),
    job_id VARCHAR NOT NULL,           -- e.g. "morning_job"
    target_agent VARCHAR NOT NULL,     -- e.g. "cell"
    target_endpoint VARCHAR NOT NULL,
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    success BOOLEAN,
    duration_ms INTEGER,
    error_type VARCHAR,                -- null | "quota_exceeded" | "timeout" | ...
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    response_payload JSONB
);

-- Provider health status
CREATE TABLE nerve_provider_status (
    provider VARCHAR PRIMARY KEY,      -- "anthropic" | "openai"
    status VARCHAR DEFAULT 'ok',       -- "ok" | "quota_exceeded" | "credits_exhausted"
    last_checked TIMESTAMPTZ DEFAULT NOW(),
    last_error TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent health tracking
CREATE TABLE nerve_agent_status (
    agent VARCHAR PRIMARY KEY,         -- "iris" | "cell" | "cortex" | "stroma"
    base_url VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'unknown',  -- "healthy" | "unreachable" | "degraded"
    last_success TIMESTAMPTZ,
    last_failure TIMESTAMPTZ,
    consecutive_failures INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
