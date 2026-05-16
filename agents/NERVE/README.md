# NERVE Orchestrator

NERVE is the deterministic backbone of the PULSE multi-agent architecture. It acts as the single source of truth for time, events, and job execution across all agents.

## Architecture
- **Zero LLM**: NERVE is entirely deterministic and rule-based.
- **Always On**: Unlike IRIS, CELL, and CORTEX (which are passive), NERVE is the only service that runs constantly.
- **Resilient**: Implements retry policies, exponential backoffs, and quota exhaustion tracking.

## Components
- `nerve/api/webhooks.py`: Receives events (e.g. `meeting.saved`) and triggers agents.
- `nerve/scheduler/cron_orchestrator.py`: `APScheduler` implementation handling all daily jobs.
- `nerve/router/forwarder.py`: The HTTP client that sends triggers and tracks agent health.
- `nerve/errors/handler.py`: Classifies agent errors (`timeout`, `agent_down`, `quota_exceeded`) and handles retry logic.

## Environment Variables
```env
DATABASE_URL=postgresql://nerve_user:nerve_pass@localhost:5432/nerve_db
IRIS_BASE_URL=http://localhost:8000
CELL_BASE_URL=http://localhost:8002
CORTEX_BASE_URL=http://localhost:8004
STROMA_BASE_URL=http://localhost:8005
NERVE_API_KEY=dev-nerve-key
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_ADMIN_CHANNEL=C12345678
TZ=Asia/Kolkata
```

## Running
```bash
# Setup Database
psql -d nerve_db -f migrations/001_nerve_schema.sql

# Install Requirements
pip install -r requirements.txt

# Run
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Testing
Unit tests are provided using standard `unittest` and `unittest.mock`.
```bash
python -m unittest tests/test_integration.py
```
