from typing import Any, Callable

from pydantic import BaseModel, Field

from app.tools.ops_tools import (
    get_recent_deployments,
    query_service_metrics,
    search_service_logs,
)


class QueryServiceMetricsArgs(BaseModel):
    service_name: str = Field(
        min_length=1,
        max_length=120,
    )

    window_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
    )


class SearchServiceLogsArgs(BaseModel):
    service_name: str = Field(
        min_length=1,
        max_length=120,
    )

    query: str = Field(
        min_length=1,
        max_length=200,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )


class GetRecentDeploymentsArgs(BaseModel):
    service_name: str = Field(
        min_length=1,
        max_length=120,
    )

    hours: int = Field(
        default=24,
        ge=1,
        le=168,
    )


class ToolExecutionError(RuntimeError):
    pass


ToolFunction = Callable[..., dict[str, Any]]


TOOL_FUNCTIONS: dict[
    str,
    ToolFunction,
] = {
    "query_service_metrics":
        query_service_metrics,

    "search_service_logs":
        search_service_logs,

    "get_recent_deployments":
        get_recent_deployments,
}


TOOL_ARGUMENT_SCHEMAS: dict[
    str,
    type[BaseModel],
] = {
    "query_service_metrics":
        QueryServiceMetricsArgs,

    "search_service_logs":
        SearchServiceLogsArgs,

    "get_recent_deployments":
        GetRecentDeploymentsArgs,
}


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    tool_function = TOOL_FUNCTIONS.get(
        tool_name
    )

    argument_schema = (
        TOOL_ARGUMENT_SCHEMAS.get(
            tool_name
        )
    )

    if (
        tool_function is None
        or argument_schema is None
    ):
        raise ToolExecutionError(
            f"Unknown tool: {tool_name}"
        )

    try:
        validated_arguments = (
            argument_schema.model_validate(
                arguments
            )
        )

        return tool_function(
            **validated_arguments.model_dump()
        )

    except Exception as exc:
        raise ToolExecutionError(
            f"Tool execution failed: {tool_name}"
        ) from exc