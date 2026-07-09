from copy import deepcopy
from typing import Any


MOCK_METRICS: dict[str, dict[str, Any]] = {
    "checkout-service": {
        "error_rate_percent": 12.8,
        "p95_latency_ms": 1840,
        "cpu_percent": 71.4,
        "memory_percent": 68.2,
        "requests_per_minute": 920,
        "database_connections_used": 96,
        "database_connections_limit": 100,
    },

    "payment-service": {
        "error_rate_percent": 3.2,
        "p95_latency_ms": 2450,
        "cpu_percent": 82.1,
        "memory_percent": 74.6,
        "requests_per_minute": 610,
        "database_connections_used": 63,
        "database_connections_limit": 100,
    },

    "auth-service": {
        "error_rate_percent": 0.7,
        "p95_latency_ms": 310,
        "cpu_percent": 46.3,
        "memory_percent": 52.8,
        "requests_per_minute": 1400,
        "database_connections_used": 34,
        "database_connections_limit": 100,
    },
}


MOCK_LOGS: dict[str, list[dict[str, str]]] = {
    "checkout-service": [
        {
            "timestamp": "2026-07-08T14:31:12Z",
            "level": "ERROR",
            "message": (
                "Database connection acquisition "
                "timed out after 5000ms"
            ),
        },
        {
            "timestamp": "2026-07-08T14:31:18Z",
            "level": "ERROR",
            "message": (
                "POST /checkout returned HTTP 500"
            ),
        },
        {
            "timestamp": "2026-07-08T14:32:03Z",
            "level": "WARN",
            "message": (
                "Connection pool utilization "
                "reached 96 percent"
            ),
        },
    ],

    "payment-service": [
        {
            "timestamp": "2026-07-08T15:10:02Z",
            "level": "WARN",
            "message": (
                "Payment provider request exceeded "
                "2000ms timeout threshold"
            ),
        },
        {
            "timestamp": "2026-07-08T15:10:10Z",
            "level": "ERROR",
            "message": (
                "Upstream payment gateway timeout"
            ),
        },
    ],

    "auth-service": [
        {
            "timestamp": "2026-07-08T16:02:01Z",
            "level": "INFO",
            "message": (
                "Token validation completed"
            ),
        },
    ],
}


MOCK_DEPLOYMENTS: dict[
    str,
    list[dict[str, str]]
] = {
    "checkout-service": [
        {
            "version": "v2.4.0",
            "deployed_at": "2026-07-08T14:29:00Z",
            "commit_sha": "a81fbc2",
            "status": "completed",
            "deployed_by": "release-bot",
        },
        {
            "version": "v2.3.7",
            "deployed_at": "2026-07-07T09:15:00Z",
            "commit_sha": "6bd911a",
            "status": "completed",
            "deployed_by": "release-bot",
        },
    ],

    "payment-service": [
        {
            "version": "v5.8.1",
            "deployed_at": "2026-07-08T08:00:00Z",
            "commit_sha": "c72aa19",
            "status": "completed",
            "deployed_by": "payments-team",
        },
    ],

    "auth-service": [],
}


def query_service_metrics(
    service_name: str,
    window_minutes: int = 30,
) -> dict[str, Any]:
    normalized_service = (
        service_name
        .strip()
        .lower()
    )

    metrics = MOCK_METRICS.get(
        normalized_service
    )

    if metrics is None:
        return {
            "source": "mock-prometheus",
            "service_name": normalized_service,
            "window_minutes": window_minutes,
            "found": False,
            "message": (
                "No metrics are available for "
                "this service."
            ),
        }

    return {
        "source": "mock-prometheus",
        "service_name": normalized_service,
        "window_minutes": window_minutes,
        "found": True,
        "metrics": deepcopy(metrics),
    }


def search_service_logs(
    service_name: str,
    query: str,
    limit: int = 20,
) -> dict[str, Any]:
    normalized_service = (
        service_name
        .strip()
        .lower()
    )

    logs = MOCK_LOGS.get(
        normalized_service,
        [],
    )

    normalized_query = (
        query
        .strip()
        .lower()
    )

    matches = [
        log
        for log in logs
        if normalized_query
        in log["message"].lower()
    ]

    if not matches:
        matches = logs

    limited_matches = matches[:limit]

    return {
        "source": "mock-log-store",
        "service_name": normalized_service,
        "query": query,
        "match_count": len(limited_matches),
        "entries": deepcopy(limited_matches),
    }


def get_recent_deployments(
    service_name: str,
    hours: int = 24,
) -> dict[str, Any]:
    normalized_service = (
        service_name
        .strip()
        .lower()
    )

    deployments = MOCK_DEPLOYMENTS.get(
        normalized_service,
        [],
    )

    return {
        "source": "mock-deployment-api",
        "service_name": normalized_service,
        "hours": hours,
        "deployment_count": len(deployments),
        "deployments": deepcopy(deployments),
    }