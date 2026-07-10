from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from typing import Literal


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


class LangChainAgentInvestigationRead(BaseModel):
    incident_id: UUID

    goal: str

    steps: list[
        AgentToolStepRead
    ]

    tool_calls_count: int

    model_calls_count: int

    final_answer: str

    model_name: str

    harness: Literal[
        "langchain_create_agent"
    ] = "langchain_create_agent"



class LangGraphAgentInvestigationRead(
    BaseModel
):
    incident_id: UUID

    goal: str

    steps: list[
        AgentToolStepRead
    ]

    tool_calls_count: int

    model_calls_count: int

    node_trace: list[str]

    final_answer: str

    stop_reason: Literal[
        "model_finished",
        "tool_budget_exhausted",
    ]

    model_name: str

    harness: Literal[
        "langgraph_state_graph"
    ] = "langgraph_state_graph"