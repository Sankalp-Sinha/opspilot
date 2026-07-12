import json

from typing import Any
from uuid import UUID

from langchain.messages import (
    HumanMessage,
    SystemMessage,
)

from app.core.config import (
    settings,
)

from app.schemas.agent_investigation import (
    PersistentLangGraphDrainRead,
    PersistentLangGraphResumeRead,
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

from app.services.ai.persistent_langgraph_agent import (
    PersistentLangGraphAgentError,
    _build_first_turn_prompt,
    _build_follow_up_prompt,
    _resolve_thread_id,
)


class PersistentLangGraphRecoveryError(
    RuntimeError
):
    pass


def _config_for_thread(
    thread_id: str,
) -> dict[str, Any]:
    return {
        "configurable": {
            "thread_id": thread_id,
        },

        "recursion_limit":
            GRAPH_RECURSION_LIMIT,
    }


def _checkpoint_id_from_snapshot(
    snapshot: Any,
) -> str | None:
    config = (
        getattr(
            snapshot,
            "config",
            None,
        )
        or {}
    )

    configurable = (
        config.get("configurable")
        or {}
    )

    checkpoint_id = (
        configurable.get(
            "checkpoint_id"
        )
    )

    if checkpoint_id is None:
        return None

    return str(checkpoint_id)


def _next_nodes_from_snapshot(
    snapshot: Any,
) -> list[str]:
    next_nodes = getattr(
        snapshot,
        "next",
        (),
    )

    return [
        str(node)
        for node in (
            next_nodes or ()
        )
    ]


def _values_from_snapshot(
    snapshot: Any,
) -> dict[str, Any]:
    values = getattr(
        snapshot,
        "values",
        None,
    )

    if isinstance(
        values,
        dict,
    ):
        return values

    return {}


def _build_input_messages(
    *,
    is_continuation: bool,
    incident_payload: dict[str, str],
    goal: str,
):
    if is_continuation:
        return [
            HumanMessage(
                content=(
                    _build_follow_up_prompt(
                        goal=goal
                    )
                )
            )
        ]

    return [
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
                )
            )
        ),
    ]


def start_persistent_langgraph_drained_run(
    *,
    incident_id: UUID,
    title: str,
    description: str,
    service_name: str | None,
    goal: str,
    thread_id: str | None,
) -> PersistentLangGraphDrainRead:
    incident_payload = {
        "title": title,

        "description": description,

        "service_name": (
            service_name
            if service_name
            else "unknown"
        ),
    }

    resolved_thread_id = (
        _resolve_thread_id(
            incident_id=incident_id,

            supplied_thread_id=thread_id,
        )
    )

    config = _config_for_thread(
        resolved_thread_id
    )

    try:
        with open_postgres_checkpointer() as (
            checkpointer
        ):
            graph = _build_incident_graph(
                checkpointer=checkpointer,
                interrupt_before=[
                    "tools",
                ],
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

            input_messages = (
                _build_input_messages(
                    is_continuation=(
                        is_continuation
                    ),

                    incident_payload=(
                        incident_payload
                    ),

                    goal=goal,
                )
            )

            graph.invoke(
                {
                    "messages":
                        input_messages,

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


            drained = True

            drain_reason = (
                "interrupted_before_tools"
            )

            snapshot_after = (
                graph.get_state(
                    config
                )
            )

            values_after = (
                _values_from_snapshot(
                    snapshot_after
                )
            )

            messages_after = (
                values_after.get(
                    "messages"
                )
                or []
            )

            return (
                PersistentLangGraphDrainRead(
                    incident_id=incident_id,

                    thread_id=(
                        resolved_thread_id
                    ),

                    drained=drained,

                    drain_reason=(
                        str(drain_reason)
                        if drain_reason
                        else None
                    ),

                    checkpoint_id=(
                        _checkpoint_id_from_snapshot(
                            snapshot_after
                        )
                    ),

                    message_count=(
                        len(messages_after)
                    ),

                    next_nodes=(
                        _next_nodes_from_snapshot(
                            snapshot_after
                        )
                    ),

                    note=(
                        "Graph drained and can be "
                        "resumed with the same "
                        "thread_id."
                        if drained
                        else (
                            "Graph completed before "
                            "drain could pause it."
                        )
                    ),
                )
            )

    except PersistentLangGraphAgentError as exc:
        raise PersistentLangGraphRecoveryError(
            str(exc)
        ) from exc

    except LangGraphAgentError as exc:
        raise PersistentLangGraphRecoveryError(
            str(exc)
        ) from exc

    except Exception as exc:
        status_code = _get_status_code(
            exc
        )

        if status_code is not None:
            raise PersistentLangGraphRecoveryError(
                "Persistent LangGraph drain "
                "request failed "
                f"({status_code}): {exc}"
            ) from exc

        raise PersistentLangGraphRecoveryError(
            "Unexpected persistent "
            "LangGraph drain error: "
            f"{type(exc).__name__}: "
            f"{exc}"
        ) from exc


def resume_persistent_langgraph_thread(
    *,
    incident_id: UUID,
    thread_id: str,
) -> PersistentLangGraphResumeRead:
    _resolve_thread_id(
        incident_id=incident_id,

        supplied_thread_id=thread_id,
    )

    config = _config_for_thread(
        thread_id
    )

    try:
        with open_postgres_checkpointer() as (
            checkpointer
        ):
            graph = _build_incident_graph(
                checkpointer=checkpointer
            )

            result = graph.invoke(
                None,
                config,
                durability="sync",
            )

            snapshot_after = (
                graph.get_state(
                    config
                )
            )

            values_after = (
                _values_from_snapshot(
                    snapshot_after
                )
            )

            messages_after = (
                values_after.get(
                    "messages"
                )
                or []
            )

            final_answer = (
                result.get("final_answer")
                or ""
            ).strip()

            if not final_answer:
                raise PersistentLangGraphRecoveryError(
                    "Resume completed without "
                    "a final answer"
                )

            stop_reason = (
                result.get("stop_reason")
            )

            if stop_reason not in {
                "model_finished",
                "tool_budget_exhausted",
            }:
                raise PersistentLangGraphRecoveryError(
                    "Resume returned invalid "
                    "stop reason"
                )

            steps = (
                result.get("steps")
                or []
            )

            return (
                PersistentLangGraphResumeRead(
                    incident_id=incident_id,

                    thread_id=thread_id,

                    checkpoint_id=(
                        _checkpoint_id_from_snapshot(
                            snapshot_after
                        )
                    ),

                    message_count=(
                        len(messages_after)
                    ),

                    next_nodes=(
                        _next_nodes_from_snapshot(
                            snapshot_after
                        )
                    ),

                    steps=steps,

                    tool_calls_count=(
                        len(steps)
                    ),

                    model_calls_count=(
                        result.get(
                            "model_calls_count",
                            0,
                        )
                        or 0
                    ),

                    node_trace=(
                        result.get(
                            "node_trace",
                            [],
                        )
                        or []
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
                        "langgraph_resume_from_checkpoint"
                    ),
                )
            )

    except PersistentLangGraphRecoveryError:
        raise

    except LangGraphAgentError as exc:
        raise PersistentLangGraphRecoveryError(
            str(exc)
        ) from exc

    except Exception as exc:
        status_code = _get_status_code(
            exc
        )

        if status_code is not None:
            raise PersistentLangGraphRecoveryError(
                "Persistent LangGraph resume "
                "request failed "
                f"({status_code}): {exc}"
            ) from exc

        raise PersistentLangGraphRecoveryError(
            "Unexpected persistent "
            "LangGraph resume error: "
            f"{type(exc).__name__}: "
            f"{exc}"
        ) from exc