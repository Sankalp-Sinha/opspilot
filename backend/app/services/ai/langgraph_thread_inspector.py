from typing import Any
from uuid import UUID

from app.schemas.agent_investigation import (
    CheckpointSummaryRead,
    PersistentThreadHistoryRead,
    PersistentThreadStateRead,
)

from app.services.ai.langgraph_agent import (
    _build_incident_graph,
)

from app.services.ai.langgraph_persistence import (
    open_postgres_checkpointer,
)


class LangGraphThreadInspectionError(
    RuntimeError
):
    pass


def _validate_thread_id(
    *,
    incident_id: UUID,
    thread_id: str,
) -> None:
    expected_prefix = (
        f"incident-{incident_id}-"
    )

    if not thread_id.startswith(
        expected_prefix
    ):
        raise LangGraphThreadInspectionError(
            "Thread ID does not belong "
            "to this incident"
        )


def _config_for_thread(
    thread_id: str,
) -> dict[str, Any]:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def _checkpoint_id_from_config(
    config: dict[str, Any] | None,
) -> str | None:
    if not config:
        return None

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


def _preview_text(
    value: Any,
    *,
    max_length: int = 240,
) -> str | None:
    if not value:
        return None

    text = str(value).strip()

    if not text:
        return None

    if len(text) <= max_length:
        return text

    return (
        text[:max_length]
        + "..."
    )


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


def _summary_from_snapshot(
    snapshot: Any,
) -> CheckpointSummaryRead:
    values = _values_from_snapshot(
        snapshot
    )

    metadata = (
        getattr(
            snapshot,
            "metadata",
            None,
        )
        or {}
    )

    config = (
        getattr(
            snapshot,
            "config",
            None,
        )
        or {}
    )

    parent_config = (
        getattr(
            snapshot,
            "parent_config",
            None,
        )
        or {}
    )

    created_at = getattr(
        snapshot,
        "created_at",
        None,
    )

    messages = (
        values.get("messages")
        or []
    )

    steps = (
        values.get("steps")
        or []
    )

    node_trace = (
        values.get("node_trace")
        or []
    )

    return CheckpointSummaryRead(
        checkpoint_id=(
            _checkpoint_id_from_config(
                config
            )
        ),

        parent_checkpoint_id=(
            _checkpoint_id_from_config(
                parent_config
            )
        ),

        created_at=(
            str(created_at)
            if created_at
            else None
        ),

        step=(
            metadata.get("step")
            if isinstance(
                metadata,
                dict,
            )
            else None
        ),

        source=(
            metadata.get("source")
            if isinstance(
                metadata,
                dict,
            )
            else None
        ),

        next_nodes=(
            _next_nodes_from_snapshot(
                snapshot
            )
        ),

        message_count=len(
            messages
        ),

        steps_count=len(
            steps
        ),

        node_trace=[
            str(node)
            for node in node_trace
        ],

        final_answer_preview=(
            _preview_text(
                values.get(
                    "final_answer"
                )
            )
        ),

        stop_reason=(
            values.get("stop_reason")
            or None
        ),
    )


def get_persistent_thread_state(
    *,
    incident_id: UUID,
    thread_id: str,
) -> PersistentThreadStateRead:
    _validate_thread_id(
        incident_id=incident_id,
        thread_id=thread_id,
    )

    config = _config_for_thread(
        thread_id
    )

    with open_postgres_checkpointer() as (
        checkpointer
    ):
        graph = _build_incident_graph(
            checkpointer=checkpointer
        )

        snapshot = graph.get_state(
            config
        )

    values = _values_from_snapshot(
        snapshot
    )

    if not values:
        raise LangGraphThreadInspectionError(
            "No checkpointed state found "
            "for this thread"
        )

    messages = (
        values.get("messages")
        or []
    )

    steps = (
        values.get("steps")
        or []
    )

    node_trace = (
        values.get("node_trace")
        or []
    )

    config_after = (
        getattr(
            snapshot,
            "config",
            None,
        )
        or {}
    )

    return PersistentThreadStateRead(
        incident_id=incident_id,

        thread_id=thread_id,

        checkpoint_id=(
            _checkpoint_id_from_config(
                config_after
            )
        ),

        message_count=len(
            messages
        ),

        next_nodes=(
            _next_nodes_from_snapshot(
                snapshot
            )
        ),

        steps_count=len(
            steps
        ),

        tool_calls_used=(
            values.get(
                "tool_calls_used",
                0,
            )
            or 0
        ),

        model_calls_count=(
            values.get(
                "model_calls_count",
                0,
            )
            or 0
        ),

        node_trace=[
            str(node)
            for node in node_trace
        ],

        final_answer_preview=(
            _preview_text(
                values.get(
                    "final_answer"
                )
            )
        ),

        stop_reason=(
            values.get("stop_reason")
            or None
        ),
    )


def get_persistent_thread_history(
    *,
    incident_id: UUID,
    thread_id: str,
    limit: int = 20,
) -> PersistentThreadHistoryRead:
    _validate_thread_id(
        incident_id=incident_id,
        thread_id=thread_id,
    )

    if limit < 1 or limit > 50:
        raise LangGraphThreadInspectionError(
            "History limit must be between "
            "1 and 50"
        )

    config = _config_for_thread(
        thread_id
    )

    with open_postgres_checkpointer() as (
        checkpointer
    ):
        graph = _build_incident_graph(
            checkpointer=checkpointer
        )

        snapshots = list(
            graph.get_state_history(
                config
            )
        )

    summaries = [
        _summary_from_snapshot(
            snapshot
        )
        for snapshot in snapshots[:limit]
    ]

    return PersistentThreadHistoryRead(
        incident_id=incident_id,

        thread_id=thread_id,

        checkpoint_count=len(
            summaries
        ),

        checkpoints=summaries,
    )