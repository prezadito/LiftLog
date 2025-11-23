"""Metrics API endpoints."""

from fastapi import APIRouter

from app.middleware.metrics import get_metrics_collector

router = APIRouter()


@router.get("/metrics")
async def get_metrics() -> dict:
    """
    Get performance metrics.

    Returns current performance metrics including:
    - Total request count
    - Per-endpoint metrics (count, errors, duration)
    - Status code distribution
    - Error count

    Note: This is a simple in-memory metrics collector.
    For production, consider using Prometheus, Cloud Monitoring, or similar.
    """
    return get_metrics_collector().get_metrics()


@router.get("/metrics/summary")
async def get_metrics_summary() -> dict:
    """
    Get high-level metrics summary.

    Returns a simplified view of key performance indicators.
    """
    metrics = get_metrics_collector().get_metrics()

    # Calculate error rate
    total_requests = metrics["total_requests"]
    total_errors = metrics["total_errors"]
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

    # Find slowest endpoint
    slowest_endpoint = None
    slowest_duration = 0
    for endpoint, data in metrics["endpoints"].items():
        if data["avg_duration_ms"] > slowest_duration:
            slowest_duration = data["avg_duration_ms"]
            slowest_endpoint = endpoint

    return {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate_percent": round(error_rate, 2),
        "slowest_endpoint": {
            "endpoint": slowest_endpoint,
            "avg_duration_ms": slowest_duration,
        } if slowest_endpoint else None,
        "status_codes": metrics["status_codes"],
    }
