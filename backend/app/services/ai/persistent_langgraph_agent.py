import json

from uuid import (
    UUID,
    uuid4,
)

from langchain.messages import (
    HumanMessage,
    SystemMessage,
)
from sqlalchemy.orm import Session

from app.schemas.memory import (
    IncidentMemoryRead,
)

from app.services.ai.memory_service import (
    format_memories_for_prompt,
    list_service_memories,
)

from app.services.ai.memory_writer import (
    maybe_write_investigation_memory,
)

from app.core.config import (
    settings,
)

from app.schemas.agent_investigation import (
    PersistentLangGraphInvestigationRead,
)

from app.services.ai.agent_loop import (
    AGENT_SYSTEM_INSTRUCTION,
)

from app.services.ai.langgraph_agent import (
    GRAPH_RECURSION_LIMIT,
    LangGraphAgentError,
    _build_incident_graph,
    _get_status_code,
)

from app.services.ai.langgraph_persistence import (
    open_postgres_checkpointer,
)


class PersistentLangGraphAgentError(
    RuntimeError
):
    pass


def _resolve_thread_id(
    *,
    incident_id: UUID,
    supplied_thread_id: str | None,
) -> str:
    prefix = (
        f"incident-{incident_id}-"
    )


    if supplied_thread_id is None:
        return (
            f"{prefix}{uuid4().hex}"
        )


    if not supplied_thread_id.startswith(
        prefix
    ):
        raise PersistentLangGraphAgentError(
            "Thread ID does not belong "
            "to this incident"
        )


    return supplied_thread_id


def _build_first_turn_prompt(
    *,
    incident_payload: dict[str, str],
    goal: str,
    memory_context: str | None = None,
) -> str:
    return (
        "Investigate the stored incident and pursue "
        "the operational goal.\n\n"

        "INCIDENT_REPORT:\n"

        f"{json.dumps(
            incident_payload,
            indent=2,
        )}"

        "\n\n"

        "LONG_TERM_SERVICE_MEMORY:\n"

        f"{memory_context or 'No durable long-term service memories are currently stored.'}"

        "\n\n"

        "Memory rules:\n"
        "1. Use long-term memory only if relevant.\n"
        "2. Live tool evidence is stronger than old memory.\n"
        "3. Do not treat memory as guaranteed truth.\n"
        "4. If memory is enough for the goal, avoid unnecessary tools.\n\n"

        "INVESTIGATION_GOAL:\n"

        f"{goal}"
    )


def _build_follow_up_prompt(
    *,
    goal: str,
    memory_context: str | None = None,
) -> str:
    return (
        "Continue the same incident investigation "
        "using relevant evidence and conclusions "
        "already present in this thread.\n\n"

        "LONG_TERM_SERVICE_MEMORY:\n"

        f"{memory_context or 'No durable long-term service memories are currently stored.'}"

        "\n\n"

        "Memory rules:\n"
        "1. Use long-term memory only if relevant.\n"
        "2. Live tool evidence in this thread is stronger than old memory.\n"
        "3. Do not repeat an earlier tool call merely "
        "to rediscover evidence already available.\n"
        "4. Call a tool only when the new goal requires additional evidence.\n\n"

        "NEW_INVESTIGATION_GOAL:\n"

        f"{goal}"
    )


def investigate_with_persistent_langgraph_agent(
    *,
    db: Session,
    workspace_id: UUID,
    incident_id: UUID,
    title: str,
    description: str,
    service_name: str | None,
    goal: str,
    thread_id: str | None,
) -> PersistentLangGraphInvestigationRead:
    incident_payload = {
        "title": title,

        "description": description,

        "service_name": (
            service_name
            if service_name
            else "unknown"
        ),
    }
    service_memories = list_service_memories(
        db=db,
        workspace_id=workspace_id,
        service_name=service_name,
        limit=5,
    )


    memory_context = format_memories_for_prompt(
        service_memories
    )


    resolved_thread_id = (
        _resolve_thread_id(
            incident_id=incident_id,

            supplied_thread_id=(
                thread_id
            ),
        )
    )


    config = {
        "configurable": {
            "thread_id":
                resolved_thread_id
        },

        "recursion_limit":
            GRAPH_RECURSION_LIMIT,
    }


    try:
        with open_postgres_checkpointer() as (
            checkpointer
        ):
            graph = _build_incident_graph(
                checkpointer=checkpointer
            )


            snapshot_before = (
                graph.get_state(
                    config
                )
            )


            previous_values = (
                snapshot_before.values
                or {}
            )


            previous_messages = (
                previous_values.get(
                    "messages"
                )
                or []
            )


            is_continuation = bool(
                previous_messages
            )


            if is_continuation:
                input_messages = [
                    HumanMessage(
                        content=(
                            _build_follow_up_prompt(
                                goal=goal,
                                memory_context=(
                                    memory_context
                                ),
                            )
                        )
                    )
                ]

            else:
                input_messages = [
                    SystemMessage(
                        content=(
                            AGENT_SYSTEM_INSTRUCTION
                        )
                    ),

                    HumanMessage(
                        content=(
                           _build_first_turn_prompt(
                                incident_payload=(
                                    incident_payload
                                ),

                                goal=goal,

                                memory_context=(
                                    memory_context
                                ),
                            )
                        )
                    ),
                ]


            result = graph.invoke(
                {
                    "messages":
                        input_messages,

                    # Current-turn execution
                    # telemetry resets here.
                    "steps": [],

                    "node_trace": [],

                    "seen_tool_calls": [],

                    "tool_calls_used": 0,

                    "model_calls_count": 0,

                    "final_answer": "",

                    "stop_reason": "",

                    "next_action": "end",
                },

                config,

                durability="sync",
            )


            final_answer = (
                result["final_answer"]
                or ""
            ).strip()


            if not final_answer:
                raise (
                    PersistentLangGraphAgentError(
                        "Persistent LangGraph "
                        "execution returned no "
                        "final answer"
                    )
                )


            stop_reason = (
                result["stop_reason"]
            )


            if stop_reason not in {
                "model_finished",
                "tool_budget_exhausted",
            }:
                raise (
                    PersistentLangGraphAgentError(
                        "Persistent LangGraph "
                        "execution returned an "
                        "invalid stop reason"
                    )
                )


            snapshot_after = (
                graph.get_state(
                    config
                )
            )


            after_values = (
                snapshot_after.values
                or {}
            )


            all_messages = (
                after_values.get(
                    "messages"
                )
                or []
            )


            configurable = (
                snapshot_after.config.get(
                    "configurable",
                    {}
                )
            )


            checkpoint_id = (
                configurable.get(
                    "checkpoint_id"
                )
            )
            checkpoint_id_text = (
                str(checkpoint_id)
                if checkpoint_id
                else None
            )


            memory_written = (
                maybe_write_investigation_memory(
                    db=db,

                    workspace_id=(
                        workspace_id
                    ),

                    incident_id=(
                        incident_id
                    ),

                    service_name=(
                        service_name
                    ),

                    goal=goal,

                    steps=result["steps"],

                    final_answer=(
                        final_answer
                    ),

                    source_thread_id=(
                        resolved_thread_id
                    ),

                    source_checkpoint_id=(
                        checkpoint_id_text
                    ),
                )
            )


            return (
                PersistentLangGraphInvestigationRead(
                    incident_id=incident_id,

                    thread_id=(
                        resolved_thread_id
                    ),

                    is_continuation=(
                        is_continuation
                    ),

                    checkpoint_id=(
                        checkpoint_id_text
                    ),

                    memories_used=[
                        IncidentMemoryRead.model_validate(
                            memory
                        )
                        for memory in service_memories
                    ],

                    memory_written=(
                        IncidentMemoryRead.model_validate(
                            memory_written
                        )
                        if memory_written
                        else None
                    ),

                    message_count=(
                        len(all_messages)
                    ),

                    goal=goal,

                    steps=result["steps"],

                    tool_calls_count=(
                        len(result["steps"])
                    ),

                    model_calls_count=(
                        result[
                            "model_calls_count"
                        ]
                    ),

                    node_trace=(
                        result[
                            "node_trace"
                        ]
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
                        "langgraph_postgres_checkpoint"
                    ),
                )
            )


    except PersistentLangGraphAgentError:
        raise


    except LangGraphAgentError as exc:
        raise (
            PersistentLangGraphAgentError(
                str(exc)
            )
        ) from exc


    except Exception as exc:
        status_code = (
            _get_status_code(
                exc
            )
        )


        if status_code is not None:
            raise (
                PersistentLangGraphAgentError(
                    "Persistent LangGraph "
                    "request failed "
                    f"({status_code}): {exc}"
                )
            ) from exc


        raise (
            PersistentLangGraphAgentError(
                "Unexpected persistent "
                "LangGraph error: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )
        ) from exc
    

    