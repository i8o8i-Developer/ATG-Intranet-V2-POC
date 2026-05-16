"""
Mock intranet employee API server.
Run standalone: python -m iris.mocks.intranet_server
Listens on port 8001 by default.
"""

from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="Mock Intranet Employee API")

# Static employee registry for testing
EMPLOYEES = {
    "p-rohan-pm": {
        "intranet_id": "p-rohan-pm",
        "name": "Rohan Sharma",
        "role": "Project Manager",
        "department": "Delivery",
        "active_projects": ["PROJ-CRM-0014", "PROJ-ECOM-0021"],
        "employment_type": "full-time",
    },
    "p-arjun-001": {
        "intranet_id": "p-arjun-001",
        "name": "Arjun Mehta",
        "role": "Backend Engineer",
        "department": "PYDJANGO",
        "active_projects": ["PROJ-CRM-0014"],
        "employment_type": "full-time",
    },
    "p-rohit-002": {
        "intranet_id": "p-rohit-002",
        "name": "Rohit Verma",
        "role": "Backend Engineer",
        "department": "PYDJANGO",
        "active_projects": ["PROJ-CRM-0014"],
        "employment_type": "full-time",
    },
    "p-dev-003": {
        "intranet_id": "p-dev-003",
        "name": "Dev Patel",
        "role": "Frontend Engineer",
        "department": "REACT",
        "active_projects": ["PROJ-CRM-0014"],
        "employment_type": "full-time",
    },
    "p-vikram-am": {
        "intranet_id": "p-vikram-am",
        "name": "Vikram Singh",
        "role": "Account Manager",
        "department": "Delivery",
        "active_projects": ["PROJ-CRM-0014"],
        "employment_type": "full-time",
    },
    "p-uiux-001": {
        "intranet_id": "p-uiux-001",
        "name": "Priya Nair",
        "role": "UI/UX Designer",
        "department": "UIUX",
        "active_projects": ["PROJ-CRM-0014"],
        "employment_type": "full-time",
    },
    "p-ba-001": {
        "intranet_id": "p-ba-001",
        "name": "Ananya Rao",
        "role": "Business Analyst",
        "department": "BA",
        "active_projects": ["PROJ-CRM-0014"],
        "employment_type": "full-time",
    },
    "hr-head": {
        "intranet_id": "hr-head",
        "name": "Sunita Kapoor",
        "role": "HR Head",
        "department": "HR",
        "active_projects": [],
        "employment_type": "full-time",
    },
    "hr-assoc-001": {
        "intranet_id": "hr-assoc-001",
        "name": "Meera Joshi",
        "role": "HR Associate",
        "department": "HR",
        "active_projects": [],
        "employment_type": "full-time",
    },
    "ceo": {
        "intranet_id": "ceo",
        "name": "Aditya Kumar",
        "role": "CEO",
        "department": "Leadership",
        "active_projects": [],
        "employment_type": "full-time",
    },
}


@app.get("/intranet/employees/{intranet_id}")
def get_employee(intranet_id: str):
    employee = EMPLOYEES.get(intranet_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {intranet_id} not found")
    return employee


@app.get("/intranet/employees")
def list_employees():
    return list(EMPLOYEES.values())


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-intranet"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
