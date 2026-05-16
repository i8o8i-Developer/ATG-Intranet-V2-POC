"""
Mock Slack API Server (port 8004).
Implements the Slack API endpoints used by CELL:
  POST /api/conversations.open   — open DM channel
  POST /api/chat.postMessage     — send message
  POST /api/conversations.history — fetch message history

Stores messages in-memory for test assertion.

Run standalone: python -m cell.mocks.slack_server
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock Slack API", version="1.0.0")

# In-memory stores
_channels: Dict[str, str] = {}           # user_id → channel_id
_messages: Dict[str, List[Dict]] = defaultdict(list)  # channel_id → [messages]


def _get_or_create_channel(user_id: str) -> str:
    if user_id not in _channels:
        _channels[user_id] = f"D{uuid.uuid4().hex[:8].upper()}"
    return _channels[user_id]


@app.post("/api/conversations.open")
async def conversations_open(request: Request) -> JSONResponse:
    body = await request.json()
    users = body.get("users", "")
    user_id = users.split(",")[0].strip() if users else "UNKNOWN"
    channel_id = _get_or_create_channel(user_id)
    return JSONResponse({"ok": True, "channel": {"id": channel_id}})


@app.post("/api/chat.postMessage")
async def chat_post_message(request: Request) -> JSONResponse:
    body = await request.json()
    channel = body.get("channel", "")
    text = body.get("text", "")
    ts = str(time.time())
    _messages[channel].append({
        "ts": ts,
        "text": text,
        "user": "BOT",
        "type": "message",
    })
    return JSONResponse({"ok": True, "ts": ts, "channel": channel})


@app.post("/api/conversations.history")
async def conversations_history(request: Request) -> JSONResponse:
    body = await request.json()
    channel = body.get("channel", "")
    oldest = float(body.get("oldest", 0))
    msgs = [m for m in _messages.get(channel, []) if float(m["ts"]) >= oldest]
    return JSONResponse({"ok": True, "messages": msgs, "response_metadata": {"next_cursor": ""}})


# ── Test helpers ──────────────────────────────────────────────

@app.post("/test/inject-message")
async def inject_message(request: Request) -> JSONResponse:
    """
    Inject a message into a user's DM channel for testing.
    Body: {"user_id": "...", "text": "..."}
    """
    body = await request.json()
    user_id = body.get("user_id")
    text = body.get("text", "")
    channel_id = _get_or_create_channel(user_id)
    ts = str(time.time())
    _messages[channel_id].append({
        "ts": ts,
        "text": text,
        "user": user_id,
        "type": "message",
    })
    return JSONResponse({"ok": True, "channel_id": channel_id, "ts": ts})


@app.get("/test/messages/{user_id}")
def get_messages(user_id: str) -> Dict[str, Any]:
    """Return all messages sent to/from a user's DM channel."""
    channel_id = _get_or_create_channel(user_id)
    return {"channel_id": channel_id, "messages": _messages.get(channel_id, [])}


@app.delete("/test/reset")
def reset() -> Dict[str, str]:
    _channels.clear()
    _messages.clear()
    return {"status": "reset"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
