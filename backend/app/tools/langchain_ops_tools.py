from typing import Any

from langchain.tools import tool

from app.tools.ops_tools import (
    get_recent_deployments as get_recent_deployments_impl,
    query_service_metrics as query_service_metrics_impl,
    search_service_logs as search_service_logs_impl,
)

from app.tools.registry import (
    GetRecentDeploymentsArgs,
    QueryServiceMetricsArgs,
    SearchServiceLogsArgs,
)


@tool(
    args_schema=QueryServiceMetricsArgs
)
def query_service_metrics(
    service_name: str,
    window_minutes: int = 30,
) -> dict[str, Any]:
    """
    Retrieve recent operational metrics for a service.

    Use this when investigating error rate, latency,
    CPU, memory, request volume, or database
    connection saturation.
    """

    return query_service_metrics_impl(
        service_name=service_name,
        window_minutes=window_minutes,
    )


@tool(
    args_schema=SearchServiceLogsArgs
)
def search_service_logs(
    service_name: str,
    query: str,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search recent service logs for runtime evidence.

    Use this when investigating errors, warnings,
    exceptions, timeouts, HTTP failures, or
    connection-related problems.
    """

    return search_service_logs_impl(
        service_name=service_name,
        query=query,
        limit=limit,
    )


@tool(
    args_schema=GetRecentDeploymentsArgs
)
def get_recent_deployments(
    service_name: str,
    hours: int = 24,
) -> dict[str, Any]:
    """
    Retrieve recent deployment history for a service.

    Use this when investigating versions, releases,
    recent code changes, or deployment correlation
    with an incident.
    """

    return get_recent_deployments_impl(
        service_name=service_name,
        hours=hours,
    )


OPS_LANGCHAIN_TOOLS = [
    query_service_metrics,
    search_service_logs,
    get_recent_deployments,
]


OPS_LANGCHAIN_TOOL_MAP = {
    ops_tool.name: ops_tool
    for ops_tool in OPS_LANGCHAIN_TOOLS
}