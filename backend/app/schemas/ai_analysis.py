from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


Severity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


IncidentCategory = Literal[
    "application",
    "database",
    "network",
    "deployment",
    "dependency",
    "security",
    "capacity",
    "unknown",
]


class IncidentAIOutput(BaseModel):
    severity: Severity = Field(
        description=(
            "Estimated operational severity based only "
            "on the supplied incident report."
        )
    )

    category: IncidentCategory = Field(
        description=(
            "Most likely incident category based only "
            "on the currently available information."
        )
    )

    affected_service: str = Field(
        min_length=1,
        max_length=120,
        description=(
            "Primary affected service, or 'unknown' "
            "if it cannot be determined."
        ),
    )

    likely_impact: str = Field(
        min_length=1,
        description=(
            "Likely user or business impact. "
            "Do not claim unverified facts."
        ),
    )

    recommended_next_step: str = Field(
        min_length=1,
        description=(
            "The single best immediate investigation "
            "step to take next."
        ),
    )

    analysis_summary: str = Field(
        min_length=1,
        description=(
            "Brief evidence-aware summary based only "
            "on the supplied incident report."
        ),
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence between 0 and 1 based on how "
            "much information the report provides."
        ),
    )


class IncidentAnalysisRead(
    IncidentAIOutput
):
    id: UUID
    incident_id: UUID

    model_name: str
    prompt_version: str

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )