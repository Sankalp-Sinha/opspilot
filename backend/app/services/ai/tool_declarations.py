from google.genai import types


QUERY_SERVICE_METRICS_DECLARATION = (
    types.FunctionDeclaration(
        name="query_service_metrics",

        description=(
            "Retrieve recent operational metrics "
            "for a service. Use this when the "
            "question concerns error rate, latency, "
            "CPU, memory, request volume, or "
            "database connection saturation."
        ),

        parameters_json_schema={
            "type": "object",

            "properties": {
                "service_name": {
                    "type": "string",
                    "description": (
                        "Exact service name, for "
                        "example checkout-service."
                    ),
                },

                "window_minutes": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 1440,
                    "description": (
                        "How many recent minutes of "
                        "metrics to inspect."
                    ),
                },
            },

            "required": [
                "service_name",
            ],
        },
    )
)


SEARCH_SERVICE_LOGS_DECLARATION = (
    types.FunctionDeclaration(
        name="search_service_logs",

        description=(
            "Search recent application logs for "
            "errors, warnings, exceptions, timeouts, "
            "or other runtime evidence. Use this "
            "when log evidence is needed."
        ),

        parameters_json_schema={
            "type": "object",

            "properties": {
                "service_name": {
                    "type": "string",
                    "description": (
                        "Exact service name."
                    ),
                },

                "query": {
                    "type": "string",
                    "description": (
                        "Short log search phrase, "
                        "for example timeout, "
                        "connection, or HTTP 500."
                    ),
                },

                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": (
                        "Maximum number of log "
                        "entries to return."
                    ),
                },
            },

            "required": [
                "service_name",
                "query",
            ],
        },
    )
)


GET_RECENT_DEPLOYMENTS_DECLARATION = (
    types.FunctionDeclaration(
        name="get_recent_deployments",

        description=(
            "Retrieve recent deployment history "
            "for a service. Use this when the "
            "question concerns releases, versions, "
            "recent code changes, or whether a "
            "deployment may correlate with an "
            "incident."
        ),

        parameters_json_schema={
            "type": "object",

            "properties": {
                "service_name": {
                    "type": "string",
                    "description": (
                        "Exact service name."
                    ),
                },

                "hours": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 168,
                    "description": (
                        "How many recent hours of "
                        "deployment history to inspect."
                    ),
                },
            },

            "required": [
                "service_name",
            ],
        },
    )
)


OPS_TOOL = types.Tool(
    function_declarations=[
        QUERY_SERVICE_METRICS_DECLARATION,
        SEARCH_SERVICE_LOGS_DECLARATION,
        GET_RECENT_DEPLOYMENTS_DECLARATION,
    ]
)