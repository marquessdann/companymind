from fastapi import APIRouter, Depends

from app.services.query_logs import get_metrics_summary
from app.security.auth import require_admin_key

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/metrics", dependencies=[Depends(require_admin_key)])
def metrics() -> dict:
    return get_metrics_summary()
