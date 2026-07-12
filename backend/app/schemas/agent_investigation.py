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



class PersistentLangGraphInvestigationRequest(
    BaseModel
):
    goal: str = Field(
        min_length=5,
        max_length=1000,
    )

    thread_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class PersistentLangGraphInvestigationRead(
    BaseModel
):
    incident_id: UUID

    thread_id: str

    is_continuation: bool

    checkpoint_id: str | None

    message_count: int

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
        "langgraph_postgres_checkpoint"
    ] = (
        "langgraph_postgres_checkpoint"
    )


class PersistentThreadStateRead(
    BaseModel
):
    incident_id: UUID

    thread_id: str

    checkpoint_id: str | None

    message_count: int

    next_nodes: list[str]

    steps_count: int

    tool_calls_used: int

    model_calls_count: int

    node_trace: list[str]

    final_answer_preview: str | None

    stop_reason: str | None


class CheckpointSummaryRead(
    BaseModel
):
    checkpoint_id: str | None

    parent_checkpoint_id: str | None

    created_at: str | None

    step: int | None

    source: str | None

    next_nodes: list[str]

    message_count: int

    steps_count: int

    node_trace: list[str]

    final_answer_preview: str | None

    stop_reason: str | None


class PersistentThreadHistoryRead(
    BaseModel
):
    incident_id: UUID

    thread_id: str

    checkpoint_count: int

    checkpoints: list[
        CheckpointSummaryRead
    ]


class PersistentLangGraphDrainRequest(
    BaseModel
):
    goal: str = Field(
        min_length=5,
        max_length=1000,
    )

    thread_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class PersistentLangGraphDrainRead(
    BaseModel
):
    incident_id: UUID

    thread_id: str

    drained: bool

    drain_reason: str | None

    checkpoint_id: str | None

    message_count: int

    next_nodes: list[str]

    note: str


class PersistentLangGraphResumeRequest(
    BaseModel
):
    thread_id: str = Field(
        min_length=1,
        max_length=255,
    )


class PersistentLangGraphResumeRead(
    BaseModel
):
    incident_id: UUID

    thread_id: str

    checkpoint_id: str | None

    message_count: int

    next_nodes: list[str]

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
        "langgraph_resume_from_checkpoint"
    ] = "langgraph_resume_from_checkpoint"