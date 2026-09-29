from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse, summary="Health Check")
def health_check():
    """
    Returns the health status of the API.
    Used by the frontend to verify backend connectivity.
    """
    return HealthResponse(
        status="healthy",
        service="AgriMarket Intelligence API",
    )
