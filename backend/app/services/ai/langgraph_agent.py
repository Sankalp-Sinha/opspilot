import json
import operator

from typing import (
    Annotated,
    Any,
    Literal,
)

from uuid import UUID

from langchain.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from langgraph.graph.message import (
    add_messages,
)

from typing_extensions import TypedDict

from app.core.config import settings

from app.schemas.agent_investigation import (
    AgentToolStepRead,
    LangGraphAgentInvestigationRead,
)

from app.services.ai.agent_loop import (
    AGENT_SYSTEM_INSTRUCTION,
    FINALIZATION_PROMPT,
    SUFFICIENCY_REMINDER,
)

from app.services.ai.langchain_model import (
    get_ops_chat_model,
)

from app.tools.langchain_ops_tools import (
    OPS_LANGCHAIN_TOOL_MAP,
    OPS_LANGCHAIN_TOOLS,
)


MAX_TOOL_STEPS = 3

GRAPH_RECURSION_LIMIT = 12


class LangGraphAgentError(
    RuntimeError
):
    pass


GraphNextAction = Literal[
    "tools",
    "finalize",
    "end",
]


GraphStopReason = Literal[
    "",
    "model_finished",
    "tool_budget_exhausted",
]


class IncidentGraphState(
    TypedDict
):
    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    steps: Annotated[
        list[AgentToolStepRead],
        operator.add,
    ]

    node_trace: Annotated[
        list[str],
        operator.add,
    ]

    seen_tool_calls: Annotated[
        list[str],
        operator.add,
    ]

    tool_calls_used: int

    model_calls_count: int

    final_answer: str

    stop_reason: GraphStopReason

    next_action: GraphNextAction


def _get_status_code(
    exc: Exception,
) -> int | None:
    status_code = getattr(
        exc,
        "status_code",
        None,
    )

    if status_code is not None:
        return status_code

    response = getattr(
        exc,
        "response",
        None,
    )

    return getattr(
        response,
        "status_code",
        None,
    )


def _get_ai_message_text(
    message: AIMessage,
) -> str:
    text = getattr(
        message,
        "text",
        "",
    )

    if isinstance(
        text,
        str,
    ):
        cleaned = text.strip()

        if cleaned:
            return cleaned

    if isinstance(
        message.content,
        str,
    ):
        return message.content.strip()

    return ""


def _build_incident_graph():
    model = get_ops_chat_model()

    model_with_tools = (
        model.bind_tools(
            OPS_LANGCHAIN_TOOLS
        )
    )


    def agent_node(
        state: IncidentGraphState,
    ) -> dict[str, Any]:
        ai_message = (
            model_with_tools.invoke(
                state["messages"]
            )
        )

        model_calls_count = (
            state["model_calls_count"]
            + 1
        )

        tool_calls = (
            ai_message.tool_calls
            or []
        )


        # Case 1:
        # Model returned final text.
        if not tool_calls:
            final_answer = (
                _get_ai_message_text(
                    ai_message
                )
            )

            if not final_answer:
                raise LangGraphAgentError(
                    "LangGraph agent node "
                    "returned empty final text"
                )

            return {
                "messages": [
                    ai_message
                ],

                "model_calls_count":
                    model_calls_count,

                "final_answer":
                    final_answer,

                "stop_reason":
                    "model_finished",

                "next_action":
                    "end",

                "node_trace": [
                    "agent"
                ],
            }


        remaining_budget = (
            MAX_TOOL_STEPS
            - state["tool_calls_used"]
        )


        # Case 2:
        # Model requested more tools than
        # our remaining application budget.
        #
        # Important:
        # We deliberately do NOT append
        # ai_message here because that would
        # leave unresolved tool calls in the
        # conversation history.
        if (
            len(tool_calls)
            > remaining_budget
        ):
            return {
                "model_calls_count":
                    model_calls_count,

                "next_action":
                    "finalize",

                "node_trace": [
                    "agent"
                ],
            }


        # Case 3:
        # Tool requests fit the budget.
        return {
            "messages": [
                ai_message
            ],

            "model_calls_count":
                model_calls_count,

            "next_action":
                "tools",

            "node_trace": [
                "agent"
            ],
        }


    def route_after_agent(
        state: IncidentGraphState,
    ) -> GraphNextAction:
        return state["next_action"]


    def tools_node(
        state: IncidentGraphState,
    ) -> dict[str, Any]:
        last_message = (
            state["messages"][-1]
        )

        if not isinstance(
            last_message,
            AIMessage,
        ):
            raise LangGraphAgentError(
                "Tools node expected the "
                "latest message to be AIMessage"
            )


        tool_calls = (
            last_message.tool_calls
            or []
        )

        if not tool_calls:
            raise LangGraphAgentError(
                "Tools node received no "
                "tool calls"
            )


        remaining_budget = (
            MAX_TOOL_STEPS
            - state["tool_calls_used"]
        )

        if (
            len(tool_calls)
            > remaining_budget
        ):
            raise LangGraphAgentError(
                "Tools node received a batch "
                "larger than remaining budget"
            )


        previously_seen = set(
            state["seen_tool_calls"]
        )

        batch_seen: set[str] = set()

        prepared_calls: list[
            tuple[
                str,
                str,
                dict[str, Any],
                Any,
                str,
            ]
        ] = []


        # Validate the complete batch first.
        # We do this before executing any tool
        # so an invalid second call does not
        # cause a partially executed batch.
        for tool_call in tool_calls:
            tool_call_id = (
                tool_call.get("id")
            )

            tool_name = (
                tool_call.get("name")
            )

            tool_arguments = (
                tool_call.get("args")
                or {}
            )


            if not tool_call_id:
                raise LangGraphAgentError(
                    "Model returned a tool "
                    "call without an ID"
                )


            if not tool_name:
                raise LangGraphAgentError(
                    "Model returned a tool "
                    "call without a name"
                )


            if not isinstance(
                tool_arguments,
                dict,
            ):
                raise LangGraphAgentError(
                    "Model returned non-object "
                    "tool arguments"
                )


            selected_tool = (
                OPS_LANGCHAIN_TOOL_MAP.get(
                    tool_name
                )
            )

            if selected_tool is None:
                raise LangGraphAgentError(
                    "Model selected unknown tool: "
                    f"{tool_name}"
                )


            tool_signature = (
                f"{tool_name}:"
                f"{json.dumps(
                    tool_arguments,
                    sort_keys=True,
                    default=str,
                )}"
            )


            if (
                tool_signature
                in previously_seen
                or tool_signature
                in batch_seen
            ):
                raise LangGraphAgentError(
                    "Agent repeated an identical "
                    "tool call; graph stopped"
                )


            batch_seen.add(
                tool_signature
            )


            prepared_calls.append(
                (
                    tool_call_id,
                    tool_name,
                    tool_arguments,
                    selected_tool,
                    tool_signature,
                )
            )


        tool_calls_used = (
            state["tool_calls_used"]
        )

        new_steps: list[
            AgentToolStepRead
        ] = []

        new_signatures: list[str] = []

        message_updates: list[
            AnyMessage
        ] = []


        for (
            tool_call_id,
            tool_name,
            tool_arguments,
            selected_tool,
            tool_signature,
        ) in prepared_calls:
            try:
                tool_result = (
                    selected_tool.invoke(
                        tool_arguments
                    )
                )

            except Exception as exc:
                raise LangGraphAgentError(
                    "LangGraph tool "
                    f"'{tool_name}' failed: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ) from exc


            if not isinstance(
                tool_result,
                dict,
            ):
                raise LangGraphAgentError(
                    f"Tool '{tool_name}' "
                    "returned a non-object result"
                )


            tool_calls_used += 1


            new_steps.append(
                AgentToolStepRead(
                    iteration=(
                        tool_calls_used
                    ),

                    tool_name=tool_name,

                    arguments=(
                        tool_arguments
                    ),

                    result=tool_result,
                )
            )


            new_signatures.append(
                tool_signature
            )


            message_updates.append(
                ToolMessage(
                    content=json.dumps(
                        {
                            "result":
                                tool_result
                        },

                        default=str,
                    ),

                    tool_call_id=(
                        tool_call_id
                    ),

                    name=tool_name,
                )
            )


        # Only add the sufficiency reminder
        # when another tool-enabled model
        # turn is still possible.
        if (
            tool_calls_used
            < MAX_TOOL_STEPS
        ):
            message_updates.append(
                HumanMessage(
                    content=(
                        SUFFICIENCY_REMINDER
                    )
                )
            )


        return {
            "messages":
                message_updates,

            "steps":
                new_steps,

            "seen_tool_calls":
                new_signatures,

            "tool_calls_used":
                tool_calls_used,

            "node_trace": [
                "tools"
            ],
        }


    def route_after_tools(
        state: IncidentGraphState,
    ) -> Literal[
        "agent",
        "finalize",
    ]:
        if (
            state["tool_calls_used"]
            >= MAX_TOOL_STEPS
        ):
            return "finalize"

        return "agent"


    def finalize_node(
        state: IncidentGraphState,
    ) -> dict[str, Any]:
        final_response = model.invoke(
            [
                *state["messages"],

                HumanMessage(
                    content=(
                        FINALIZATION_PROMPT
                    )
                ),
            ]
        )


        final_answer = (
            _get_ai_message_text(
                final_response
            )
        )


        if not final_answer:
            raise LangGraphAgentError(
                "LangGraph finalize node "
                "returned empty text"
            )


        return {
            "messages": [
                final_response
            ],

            "model_calls_count": (
                state["model_calls_count"]
                + 1
            ),

            "final_answer":
                final_answer,

            "stop_reason":
                "tool_budget_exhausted",

            "next_action":
                "end",

            "node_trace": [
                "finalize"
            ],
        }


    builder = StateGraph(
        IncidentGraphState
    )


    builder.add_node(
        "agent",
        agent_node,
    )

    builder.add_node(
        "tools",
        tools_node,
    )

    builder.add_node(
        "finalize",
        finalize_node,
    )


    builder.add_edge(
        START,
        "agent",
    )


    builder.add_conditional_edges(
        "agent",

        route_after_agent,

        {
            "tools":
                "tools",

            "finalize":
                "finalize",

            "end":
                END,
        },
    )


    builder.add_conditional_edges(
        "tools",

        route_after_tools,

        {
            "agent":
                "agent",

            "finalize":
                "finalize",
        },
    )


    builder.add_edge(
        "finalize",
        END,
    )


    return builder.compile()


def investigate_with_langgraph_agent(
    *,
    incident_id: UUID,
    title: str,
    description: str,
    service_name: str | None,
    goal: str,
) -> LangGraphAgentInvestigationRead:
    incident_payload = {
        "title": title,

        "description": description,

        "service_name": (
            service_name
            if service_name
            else "unknown"
        ),
    }


    user_prompt = (
        "Investigate the stored incident and pursue "
        "the operational goal.\n\n"

        "INCIDENT_REPORT:\n"

        f"{json.dumps(
            incident_payload,
            indent=2,
        )}"

        "\n\n"

        "INVESTIGATION_GOAL:\n"

        f"{goal}"
    )


    try:
        graph = _build_incident_graph()


        result = graph.invoke(
            {
                "messages": [
                    SystemMessage(
                        content=(
                            AGENT_SYSTEM_INSTRUCTION
                        )
                    ),

                    HumanMessage(
                        content=user_prompt
                    ),
                ],

                "steps": [],

                "node_trace": [],

                "seen_tool_calls": [],

                "tool_calls_used": 0,

                "model_calls_count": 0,

                "final_answer": "",

                "stop_reason": "",

                "next_action": "end",
            },

            {
                "recursion_limit":
                    GRAPH_RECURSION_LIMIT
            },
        )


        final_answer = (
            result["final_answer"]
            or ""
        ).strip()


        if not final_answer:
            raise LangGraphAgentError(
                "LangGraph execution returned "
                "no final answer"
            )


        stop_reason = (
            result["stop_reason"]
        )


        if stop_reason not in {
            "model_finished",
            "tool_budget_exhausted",
        }:
            raise LangGraphAgentError(
                "LangGraph execution returned "
                "an invalid stop reason"
            )


        return (
            LangGraphAgentInvestigationRead(
                incident_id=incident_id,

                goal=goal,

                steps=result["steps"],

                tool_calls_count=len(
                    result["steps"]
                ),

                model_calls_count=(
                    result[
                        "model_calls_count"
                    ]
                ),

                node_trace=(
                    result["node_trace"]
                ),

                final_answer=(
                    final_answer
                ),

                stop_reason=(
                    stop_reason
                ),

                model_name=(
                    settings.groq_model
                ),

                harness=(
                    "langgraph_state_graph"
                ),
            )
        )


    except LangGraphAgentError:
        raise


    except Exception as exc:
        status_code = _get_status_code(
            exc
        )


        if status_code is not None:
            raise LangGraphAgentError(
                "LangGraph model request "
                "failed "
                f"({status_code}): {exc}"
            ) from exc


        raise LangGraphAgentError(
            "Unexpected LangGraph error: "
            f"{type(exc).__name__}: "
            f"{exc}"
        ) from exc