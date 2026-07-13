from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


MemoryType = Literal[
    "operational_pattern",
    "known_signal",
    "likely_cause",
    "remediation_hint",
    "risk",
    "other",
]


class IncidentMemoryRead(BaseModel):
    id: UUID

    workspace_id: UUID

    incident_id: UUID | None

    service_name: str

    memory_type: str

    summary: str

    evidence: str

    confidence: float

    source_thread_id: str | None

    source_checkpoint_id: str | None

    is_active: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class IncidentMemoryListRead(BaseModel):
    incident_id: UUID

    workspace_id: UUID

    service_name: str | None

    memories: list[
        IncidentMemoryRead
    ]


class MemoryWriteDecision(BaseModel):
    should_store: bool = Field(
        description=(
            "Whether this investigation produced "
            "durable operational memory worth "
            "using in future threads."
        )
    )

    memory_type: MemoryType = Field(
        default="operational_pattern",
    )

    summary: str = Field(
        min_length=1,
        max_length=500,
        description=(
            "Reusable operational learning. "
            "Do not include unsupported claims."
        ),
    )

    evidence: str = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Concrete evidence supporting the memory."
        ),
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )