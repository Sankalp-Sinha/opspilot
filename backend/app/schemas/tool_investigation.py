from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ToolInvestigationRequest(BaseModel):
    question: str = Field(
        min_length=5,
        max_length=500,
    )


class ToolExecutionRead(BaseModel):
    name: str

    arguments: dict[str, Any]

    result: dict[str, Any]


class ToolInvestigationRead(BaseModel):
    incident_id: UUID

    question: str

    tool_called: bool

    tool_execution: ToolExecutionRead | None

    final_answer: str

    model_name: str