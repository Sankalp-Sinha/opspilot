import hashlib

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident_memory import (
    IncidentMemory,
)


def _normalize_for_hash(
    value: str,
) -> str:
    return " ".join(
        value.lower().strip().split()
    )


def build_memory_hash(
    *,
    service_name: str,
    summary: str,
) -> str:
    raw = (
        f"{_normalize_for_hash(service_name)}:"
        f"{_normalize_for_hash(summary)}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def list_service_memories(
    *,
    db: Session,
    workspace_id: UUID,
    service_name: str | None,
    limit: int = 5,
) -> list[IncidentMemory]:
    if not service_name:
        return []

    statement = (
        select(IncidentMemory)
        .where(
            IncidentMemory.workspace_id
            == workspace_id,

            IncidentMemory.service_name
            == service_name,

            IncidentMemory.is_active
            == True,  # noqa: E712
        )
        .order_by(
            IncidentMemory.updated_at.desc()
        )
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


def save_incident_memory(
    *,
    db: Session,
    workspace_id: UUID,
    incident_id: UUID,
    service_name: str,
    memory_type: str,
    summary: str,
    evidence: str,
    confidence: float,
    source_thread_id: str | None,
    source_checkpoint_id: str | None,
) -> IncidentMemory:
    memory_hash = build_memory_hash(
        service_name=service_name,
        summary=summary,
    )


    existing = db.scalar(
        select(IncidentMemory).where(
            IncidentMemory.workspace_id
            == workspace_id,

            IncidentMemory.service_name
            == service_name,

            IncidentMemory.memory_hash
            == memory_hash,
        )
    )


    if existing is not None:
        existing.memory_type = memory_type
        existing.evidence = evidence
        existing.confidence = confidence
        existing.source_thread_id = (
            source_thread_id
        )
        existing.source_checkpoint_id = (
            source_checkpoint_id
        )
        existing.is_active = True
        existing.updated_at = datetime.now(
            timezone.utc
        )

        db.commit()
        db.refresh(existing)

        return existing


    memory = IncidentMemory(
        workspace_id=workspace_id,
        incident_id=incident_id,
        service_name=service_name,
        memory_type=memory_type,
        summary=summary,
        evidence=evidence,
        confidence=confidence,
        source_thread_id=source_thread_id,
        source_checkpoint_id=(
            source_checkpoint_id
        ),
        memory_hash=memory_hash,
        is_active=True,
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory


def format_memories_for_prompt(
    memories: list[IncidentMemory],
) -> str:
    if not memories:
        return (
            "No durable long-term service "
            "memories are currently stored."
        )


    lines: list[str] = []

    for index, memory in enumerate(
        memories,
        start=1,
    ):
        lines.append(
            (
                f"{index}. "
                f"[{memory.memory_type}, "
                f"confidence={memory.confidence:.2f}] "
                f"{memory.summary}\n"
                f"Evidence: {memory.evidence}"
            )
        )


    return "\n\n".join(lines)