from typing import Any


OPS_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",

        "function": {
            "name": "query_service_metrics",

            "description": (
                "Retrieve recent operational metrics "
                "for a service. Use this when the "
                "investigation concerns error rate, "
                "latency, CPU, memory, request volume, "
                "or database connection saturation."
            ),

            "parameters": {
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
                            "How many recent minutes "
                            "of metrics to inspect."
                        ),
                    },
                },

                "required": [
                    "service_name",
                ],
            },
        },
    },

    {
        "type": "function",

        "function": {
            "name": "search_service_logs",

            "description": (
                "Search recent application logs for "
                "errors, warnings, exceptions, "
                "timeouts, or runtime evidence. "
                "Use this when log evidence is needed."
            ),

            "parameters": {
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
        },
    },

    {
        "type": "function",

        "function": {
            "name": "get_recent_deployments",

            "description": (
                "Retrieve recent deployment history "
                "for a service. Use this when the "
                "investigation concerns releases, "
                "versions, recent code changes, or "
                "whether deployment activity may "
                "correlate with an incident."
            ),

            "parameters": {
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
                            "deployment history to "
                            "inspect."
                        ),
                    },
                },

                "required": [
                    "service_name",
                ],
            },
        },
    },
]