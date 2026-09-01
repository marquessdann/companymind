from fastapi import APIRouter

from app.services.query_logs import get_metrics_summary

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict:
    return get_metrics_summary()
