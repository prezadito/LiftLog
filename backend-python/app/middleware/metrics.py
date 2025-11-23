"""Metrics collection middleware for monitoring."""

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.request_count: defaultdict[str, int] = defaultdict(int)
        self.request_duration: defaultdict[str, list[float]] = defaultdict(list)
        self.error_count: defaultdict[str, int] = defaultdict(int)
        self.status_codes: defaultdict[int, int] = defaultdict(int)

    def record_request(
        self, method: str, path: str, status_code: int, duration_ms: float
    ) -> None:
        """Record request metrics."""
        endpoint = f"{method} {path}"

        # Increment request count
        self.request_count[endpoint] += 1

        # Record duration
        self.request_duration[endpoint].append(duration_ms)

        # Keep only last 1000 durations to prevent memory issues
        if len(self.request_duration[endpoint]) > 1000:
            self.request_duration[endpoint] = self.request_duration[endpoint][-1000:]

        # Record status code
        self.status_codes[status_code] += 1

        # Record errors (4xx and 5xx)
        if status_code >= 400:
            self.error_count[endpoint] += 1

    def get_metrics(self) -> dict:
        """Get current metrics summary."""
        metrics = {
            "total_requests": sum(self.request_count.values()),
            "endpoints": {},
            "status_codes": dict(self.status_codes),
            "total_errors": sum(self.error_count.values()),
        }

        # Calculate per-endpoint metrics
        for endpoint, count in self.request_count.items():
            durations = self.request_duration[endpoint]
            if durations:
                avg_duration = sum(durations) / len(durations)
                p95_duration = sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else avg_duration
                p99_duration = sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 100 else avg_duration
            else:
                avg_duration = 0
                p95_duration = 0
                p99_duration = 0

            metrics["endpoints"][endpoint] = {
                "count": count,
                "errors": self.error_count[endpoint],
                "avg_duration_ms": round(avg_duration, 2),
                "p95_duration_ms": round(p95_duration, 2),
                "p99_duration_ms": round(p99_duration, 2),
            }

        return metrics

    def log_metrics(self) -> None:
        """Log current metrics."""
        metrics = self.get_metrics()

        logger.info(
            "Performance metrics",
            extra={
                "total_requests": metrics["total_requests"],
                "total_errors": metrics["total_errors"],
                "status_codes": metrics["status_codes"],
            },
        )

        # Log top 10 slowest endpoints
        slowest_endpoints = sorted(
            metrics["endpoints"].items(),
            key=lambda x: x[1]["avg_duration_ms"],
            reverse=True,
        )[:10]

        if slowest_endpoints:
            logger.info(
                "Slowest endpoints",
                extra={"endpoints": dict(slowest_endpoints)},
            )


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect performance metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record metrics
            get_metrics_collector().record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record error metric
            get_metrics_collector().record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
            )

            # Re-raise the exception
            raise
