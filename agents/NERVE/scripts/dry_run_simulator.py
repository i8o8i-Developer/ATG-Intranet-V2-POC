import asyncio
import httpx
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Header, Request
from pydantic import BaseModel
import asyncpg
import json
import uuid
from datetime import datetime, timezone

# We'll use colorama for pretty output
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name): return ""
    Fore = Style = DummyColor()

app = FastAPI(title="PULSE Mock Agents")

import os
from dotenv import load_dotenv

load_dotenv()

# NERVE endpoint remains hardcoded for simulation routing logic
NERVE_API_URL = "http://localhost:8001/nerve/event"

# Secrets loaded from .env
NERVE_API_KEY = os.getenv("NERVE_API_KEY", "dev-nerve-key")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print(f"{Fore.RED}DATABASE_URL missing from .env")
    exit(1)

def print_banner(title: str, color=Fore.CYAN):
    print(f"\n{color}{Style.BRIGHT}{'='*60}")
    print(f"{color}{Style.BRIGHT} {title}")
    print(f"{color}{Style.BRIGHT}{'='*60}")

# --- MOCK AGENT ENDPOINTS ---

@app.post("/iris/trigger")
async def mock_iris_trigger(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    print(f"{Fore.MAGENTA}[IRIS] Intercepted event: {payload.get('event')} for meeting: {payload.get('meeting_id')}")
    
    # Simulate processing time, then fire extraction complete
    background_tasks.add_task(simulate_extraction, payload)
    return {"success": True, "status": "processing"}

async def simulate_extraction(payload: dict):
    await asyncio.sleep(1.5)
    print(f"{Fore.MAGENTA}[IRIS] Finished extraction. Emitting 'iris.extraction.complete' to NERVE...")
    
    fake_payload = {
        "event": "iris.extraction.complete",
        "meeting_id": payload.get("meeting_id", f"meet_{uuid.uuid4().hex[:8]}"),
        "project_id": payload.get("project_id", f"proj_{uuid.uuid4().hex[:8]}"),
        "confidence_score": 0.94,
        "flagged": False,
        "insights_path": "s3://mock-bucket/insights.json",
        "provider": "anthropic"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                NERVE_API_URL, 
                json=fake_payload,
                headers={"X-API-Key": NERVE_API_KEY}
            )
            print(f"{Fore.MAGENTA}[IRIS] NERVE acknowledged callback with status: {resp.status_code}")
        except Exception as e:
            print(f"{Fore.RED}[IRIS] Failed to hit NERVE: {e}")

@app.post("/cell/ingest-nerve")
async def mock_cell_ingest(request: Request):
    payload = await request.json()
    print(f"{Fore.GREEN}[CELL] Intercepted fan-out payload:")
    print(f"{Fore.GREEN}{json.dumps(payload, indent=2)}")
    return {"success": True}

@app.post("/cell/jobs/{job_name}")
async def mock_cell_job(job_name: str, request: Request):
    payload = await request.json()
    print(f"{Fore.GREEN}[CELL] Intercepted job trigger for: {job_name}")
    print(f"{Fore.GREEN}{json.dumps(payload, indent=2)}")
    # Simulate work
    await asyncio.sleep(0.5)
    return {
        "success": True, 
        "job": job_name,
        "duration_ms": 500,
        "error": None,
        "details": {"processed_items": 42}
    }

@app.post("/cortex/ingest-nerve")
async def mock_cortex_ingest(request: Request):
    payload = await request.json()
    print(f"{Fore.BLUE}[CORTEX] Intercepted fan-out payload:")
    print(f"{Fore.BLUE}{json.dumps(payload, indent=2)}")
    return {"success": True}

# --- DATABASE INTERCEPTION ---

async def intercept_database():
    print_banner("DATABASE INTERCEPTION (SCHEMAS & STATE)", Fore.YELLOW)
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print(f"{Fore.GREEN}Successfully connected to Postgres. Fetching real schemas and state...")
        
        # --- INTERCEPT SCHEMAS ---
        tables = ['nerve_event_log', 'nerve_job_log', 'nerve_agent_status', 'nerve_provider_status']
        print(f"{Fore.YELLOW}{Style.BRIGHT}--- DATABASE SCHEMAS ---")
        for table in tables:
            schema_query = f"""
                SELECT column_name, data_type, character_maximum_length, column_default, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            """
            columns = await conn.fetch(schema_query)
            print(f"\n{Fore.CYAN}Table: {table}")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  {col['column_name']} ({col['data_type']}) {nullable} {default}")

        # --- INTERCEPT ITEMS ---
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}--- DATABASE ITEMS (STATE) ---")
        
        print(f"{Fore.YELLOW}{Style.BRIGHT}Table: nerve_event_log (Latest 5)")
        rows = await conn.fetch("SELECT id, event_type, source, status, details FROM nerve_event_log ORDER BY id DESC LIMIT 5")
        for row in rows:
            print(f"{Fore.YELLOW}ID: {row['id']} | Event: {row['event_type']} | Source: {row['source']} | Status: {row['status']}")
            details = json.loads(row['details'])
            if 'meeting_id' in details:
                print(f"       Meeting ID: {details['meeting_id']}")

        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Table: nerve_agent_status")
        agents = await conn.fetch("SELECT agent, status, consecutive_failures, last_success FROM nerve_agent_status")
        for a in agents:
            print(f"{Fore.YELLOW}Agent: {a['agent']} | Status: {a['status']} | Failures: {a['consecutive_failures']}")
            
        await conn.close()
        
    except Exception as e:
        print(f"{Fore.RED}Postgres not available. Displaying hardcoded intercept for schemas & items.")
        print(f"\n{Fore.CYAN}Table: nerve_event_log")
        print("  id (integer) NOT NULL DEFAULT nextval('nerve_event_log_id_seq')")
        print("  timestamp (timestamp with time zone) NULL DEFAULT now()")
        print("  event_type (character varying) NOT NULL ")
        print("  source (character varying) NULL ")
        print("  details (jsonb) NULL ")
        print("  status (character varying) NULL DEFAULT 'received'")
        print(f"\n{Fore.CYAN}Table: nerve_job_log")
        print("  id (integer) NOT NULL DEFAULT nextval('nerve_job_log_id_seq')")
        print("  trigger_id (uuid) NOT NULL DEFAULT gen_random_uuid()")
        print("  job_id (character varying) NOT NULL ")
        print("  target_agent (character varying) NOT NULL ")
        print("  success (boolean) NULL ")
        
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}--- MOCKED DATABASE ITEMS (STATE) ---")
        print(f"{Fore.YELLOW}ID: 2 | Event: iris.extraction.complete | Source: external | Status: completed")
        print(f"       Meeting ID: meet_demo_XXXXXX")
        print(f"{Fore.YELLOW}ID: 1 | Event: meeting.saved | Source: external | Status: completed")
        print(f"       Meeting ID: meet_demo_XXXXXX")
        
        print(f"\n{Fore.YELLOW}Agent: iris | Status: unknown | Failures: 0")
        print(f"{Fore.YELLOW}Agent: cell | Status: unknown | Failures: 0")
        print(f"{Fore.YELLOW}Agent: cortex | Status: unknown | Failures: 0")

# --- RUNNER ---

async def run_simulation():
    print_banner("STARTING DRY-RUN SIMULATOR", Fore.CYAN)
    print("1. Please ensure NERVE is running on port 8001")
    print("2. Please ensure NERVE is configured to point IRIS, CELL, CORTEX to port 9999")
    print("Waiting 2 seconds for server boot...")
    await asyncio.sleep(2)
    
    # Since Backend hits IRIS directly, IRIS acts as the event emitter to NERVE.
    # We simulate IRIS finishing extraction and hitting NERVE:
    print_banner("SIMULATING IRIS EMITTING extraction.complete TO NERVE")
    event_payload = {
        "event": "iris.extraction.complete",
        "source": "iris",
        "project_id": "proj_demo_551a7e",
        "meeting_id": "meet_demo_6638f5",
        "confidence_score": 0.94,
        "flagged": False,
        "insights_path": "s3://mock-bucket/insights.json",
        "provider": "anthropic",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                NERVE_API_URL, 
                json=event_payload,
                headers={"X-API-Key": NERVE_API_KEY}
            )
            print(f"NERVE Event Response: {resp.status_code}")
        except Exception as e:
            print(f"{Fore.RED}Failed to reach NERVE at {NERVE_API_URL}. Is it running?")
            return

    print_banner("TESTING JOB TRIGGER (SUCCESS)", Fore.CYAN)
    print("Manually triggering 'morning_job' on CELL via Admin API...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://localhost:8001/nerve/jobs/trigger/morning_job",
                headers={"X-API-Key": NERVE_API_KEY}
            )
            print(f"NERVE Job Response (CELL): {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"{Fore.RED}Failed to trigger job: {e}")

    print_banner("TESTING JOB TRIGGER (FAILURE - AGENT DOWN)", Fore.CYAN)
    print("Manually triggering 'stroma_capacity_sync' on STROMA (which is down)...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://localhost:8001/nerve/jobs/trigger/stroma_capacity_sync",
                headers={"X-API-Key": NERVE_API_KEY}
            )
            print(f"NERVE Job Response (STROMA): {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"{Fore.RED}Failed to trigger STROMA job: {e}")

    # Wait for the async flow to finish (IRIS processing + fanout + retries)
    print("\nWaiting 5 seconds for asynchronous event propagation and job retries...")
    await asyncio.sleep(5)
    
    # Intercept Database
    await intercept_database()
    print_banner("SIMULATION COMPLETE", Fore.GREEN)
    
    # Stop the server cleanly
    import os
    os._exit(0)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_simulation())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999, log_level="error")
