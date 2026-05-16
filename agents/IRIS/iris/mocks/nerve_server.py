"""
Mock NERVE event receiver.
Run standalone: python -m iris.mocks.nerve_server
Listens on port 8002 by default. Logs all received events.
"""

from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import json

app = FastAPI(title="Mock NERVE Event Receiver")

received_events: list[dict] = []


@app.post("/events")
async def receive_event(request: Request):
    body = await request.json()
    entry = {
        "received_at": datetime.utcnow().isoformat(),
        "payload": body,
    }
    received_events.append(entry)
    print(f"\n[NERVE] Event received at {entry['received_at']}:")
    print(json.dumps(body, indent=2))
    return {"status": "received", "event_count": len(received_events)}


@app.get("/events")
def list_events():
    """Inspect all events NERVE has received — useful for test assertions."""
    return {"events": received_events, "count": len(received_events)}


@app.delete("/events")
def clear_events():
    """Reset event log — call between tests."""
    received_events.clear()
    return {"status": "cleared"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-nerve"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
