from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
    )

    slug: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9-]+$",
    )


class WorkspaceRead(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )