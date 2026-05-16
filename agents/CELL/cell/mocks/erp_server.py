"""
Mock ERP API Server (port 8003).
Supports:
  POST   /api/tasks              — create task → returns erp_task_id
  PATCH  /api/tasks/{id}        — update status/notes
  GET    /api/tasks              — list tasks (filter by project_id, assignee_id, status)

Run standalone: python -m cell.mocks.erp_server
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Mock ERP API", version="1.0.0")

# In-memory store
_tasks: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-erp"}


@app.post("/api/tasks", status_code=201)
def create_task(body: dict) -> Dict[str, Any]:
    erp_id = f"ERP-{uuid.uuid4().hex[:8].upper()}"
    task = {
        "erp_task_id": erp_id,
        "title": body.get("title"),
        "project_id": body.get("project_id"),
        "assignee_id": body.get("assignee_id"),
        "priority": body.get("priority", "normal"),
        "estimated_hours": body.get("estimated_hours", 4),
        "bounty_value": body.get("bounty_value", 1.0),  # bounty units
        "status": body.get("status", "open"),
        "due_date": body.get("due_date"),
        "notes": body.get("notes"),
        "source_meeting_id": body.get("source_meeting_id"),
        "source_yaml_field": body.get("source_yaml_field"),
        "subtasks": body.get("subtasks", []),
    }
    _tasks[erp_id] = task
    return task


@app.patch("/api/tasks/{erp_task_id}")
def update_task(erp_task_id: str, body: dict) -> Dict[str, Any]:
    if erp_task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    _tasks[erp_task_id].update(body)
    return _tasks[erp_task_id]


@app.get("/api/tasks")
def list_tasks(
    project_id: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> Dict[str, Any]:
    tasks = list(_tasks.values())
    if project_id:
        tasks = [t for t in tasks if t.get("project_id") == project_id]
    if assignee_id:
        tasks = [t for t in tasks if t.get("assignee_id") == assignee_id]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return {"tasks": tasks, "count": len(tasks)}


@app.get("/api/tasks/{erp_task_id}")
def get_task(erp_task_id: str) -> Dict[str, Any]:
    if erp_task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[erp_task_id]


@app.delete("/api/tasks")
def clear_tasks() -> Dict[str, str]:
    """Test helper — clear all tasks."""
    _tasks.clear()
    return {"status": "cleared"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
