import json

from uuid import UUID

from langchain.messages import (
    HumanMessage,
    SystemMessage,
)

from sqlalchemy.orm import Session

from app.schemas.memory import (
    MemoryWriteDecision,
)

from app.schemas.agent_investigation import (
    AgentToolStepRead,
)

from app.services.ai.langchain_model import (
    get_ops_chat_model,
)

from app.services.ai.memory_service import (
    save_incident_memory,
)


MEMORY_WRITER_SYSTEM_PROMPT = """
You are OpsPilot's long-term memory writer.

Your job is to decide whether an incident investigation
created durable operational knowledge that should be
available to future investigation threads.

Store memory only if it is:
1. reusable across future incidents,
2. supported by concrete evidence,
3. about service behavior, symptoms, likely causes,
   remediation hints, risks, or known operational signals.

Do not store:
1. one-off user instructions,
2. unsupported guesses,
3. generic advice,
4. exact temporary request wording,
5. facts not supported by the investigation evidence.

The memory must be concise, factual, and useful for
future incident response.
""".strip()


def _steps_to_payload(
    steps: list[AgentToolStepRead],
) -> list[dict]:
    return [
        {
            "tool_name": step.tool_name,
            "arguments": step.arguments,
            "result": step.result,
        }
        for step in steps
    ]


def maybe_write_investigation_memory(
    *,
    db: Session,
    workspace_id: UUID,
    incident_id: UUID,
    service_name: str | None,
    goal: str,
    steps: list[AgentToolStepRead],
    final_answer: str,
    source_thread_id: str | None,
    source_checkpoint_id: str | None,
):
    if not service_name:
        return None


    payload = {
        "service_name": service_name,
        "goal": goal,
        "steps": _steps_to_payload(
            steps
        ),
        "final_answer": final_answer,
    }


    try:
        model = get_ops_chat_model()

        structured_model = (
            model.with_structured_output(
                MemoryWriteDecision
            )
        )

        decision = structured_model.invoke(
            [
                SystemMessage(
                    content=(
                        MEMORY_WRITER_SYSTEM_PROMPT
                    )
                ),

                HumanMessage(
                    content=(
                        "Decide whether to write "
                        "long-term operational memory "
                        "from this investigation.\n\n"
                        f"{json.dumps(payload, indent=2, default=str)}"
                    )
                ),
            ]
        )


        if not isinstance(
            decision,
            MemoryWriteDecision,
        ):
            return None


        if not decision.should_store:
            return None


        if decision.confidence < 0.65:
            return None


        return save_incident_memory(
            db=db,
            workspace_id=workspace_id,
            incident_id=incident_id,
            service_name=service_name,
            memory_type=decision.memory_type,
            summary=decision.summary,
            evidence=decision.evidence,
            confidence=decision.confidence,
            source_thread_id=source_thread_id,
            source_checkpoint_id=(
                source_checkpoint_id
            ),
        )


    except Exception as exc:
        print(
            "MEMORY WRITE SKIPPED:",
            type(exc).__name__,
            str(exc),
        )

        return None