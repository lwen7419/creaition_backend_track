from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.utils.time import utc_now_iso

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=utc_now_iso())
