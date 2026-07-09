from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


AgentStopReason = Literal[
    "model_finished",
    "tool_budget_exhausted",
]


class AgentInvestigationRequest(BaseModel):
    goal: str = Field(
        min_length=5,
        max_length=1000,
    )


class AgentToolStepRead(BaseModel):
    iteration: int

    tool_name: str

    arguments: dict[str, Any]

    result: dict[str, Any]


class AgentInvestigationRead(BaseModel):
    run_id: UUID

    incident_id: UUID

    goal: str

    status: Literal["completed"]

    steps: list[AgentToolStepRead]

    tool_calls_count: int

    final_answer: str

    stop_reason: AgentStopReason

    model_name: str