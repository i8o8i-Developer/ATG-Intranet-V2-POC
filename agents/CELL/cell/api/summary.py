from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/cell")

class SummaryResponse(BaseModel):
    project_id: str
    status: str
    velocity: float
    message: str

@router.get("/summary/{project_id}")
async def get_project_summary(project_id: str):
    """
    Returns EOD summary data for the last 7 days for a given project.
    Used by CORTEX for weekly aggregation.
    """
    # Placeholder implementation
    return SummaryResponse(
        project_id=project_id,
        status="active",
        velocity=1.5,
        message="Summary data available"
    )
