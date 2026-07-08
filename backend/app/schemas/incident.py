from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    workspace_id: UUID

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=3,
    )

    service_name: str | None = Field(
        default=None,
        max_length=120,
    )


class IncidentRead(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    description: str
    service_name: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )