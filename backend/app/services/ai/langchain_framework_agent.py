import json

from ast import literal_eval
from typing import Any
from uuid import UUID

from langchain.agents import (
    create_agent,
)

from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
)

from langchain.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)

from app.core.config import settings

from app.schemas.agent_investigation import (
    AgentToolStepRead,
    LangChainAgentInvestigationRead,
)

from app.services.ai.agent_loop import (
    AGENT_SYSTEM_INSTRUCTION,
)

from app.services.ai.langchain_model import (
    get_ops_chat_model,
)

from app.tools.langchain_ops_tools import (
    OPS_LANGCHAIN_TOOLS,
)


MAX_MODEL_CALLS = 4


class LangChainFrameworkAgentError(
    RuntimeError
):
    pass


def _get_status_code(
    exc: Exception,
) -> int | None:
    status_code = getattr(
        exc,
        "status_code",
        None,
    )

    if status_code is not None:
        return status_code

    response = getattr(
        exc,
        "response",
        None,
    )

    return getattr(
        response,
        "status_code",
        None,
    )


def _normalize_tool_result(
    value: Any,
) -> dict[str, Any]:
    if isinstance(
        value,
        dict,
    ):
        return value


    if isinstance(
        value,
        str,
    ):
        stripped = value.strip()


        try:
            parsed_json = json.loads(
                stripped
            )

            if isinstance(
                parsed_json,
                dict,
            ):
                return parsed_json

            return {
                "output": parsed_json
            }

        except json.JSONDecodeError:
            pass


        try:
            parsed_literal = literal_eval(
                stripped
            )

            if isinstance(
                parsed_literal,
                dict,
            ):
                return parsed_literal

            return {
                "output":
                    parsed_literal
            }

        except (
            ValueError,
            SyntaxError,
        ):
            return {
                "output": value
            }


    return {
        "output": value
    }


def _get_ai_message_text(
    message: AIMessage,
) -> str:
    text = getattr(
        message,
        "text",
        "",
    )

    if isinstance(
        text,
        str,
    ):
        cleaned = text.strip()

        if cleaned:
            return cleaned


    if isinstance(
        message.content,
        str,
    ):
        return (
            message.content.strip()
        )


    return ""


def investigate_with_langchain_agent(
    *,
    incident_id: UUID,
    title: str,
    description: str,
    service_name: str | None,
    goal: str,
) -> LangChainAgentInvestigationRead:
    incident_payload = {
        "title": title,

        "description": description,

        "service_name": (
            service_name
            if service_name
            else "unknown"
        ),
    }


    user_prompt = (
        "Investigate the stored incident and pursue "
        "the operational goal.\n\n"

        "INCIDENT_REPORT:\n"

        f"{json.dumps(
            incident_payload,
            indent=2,
        )}"

        "\n\n"

        "INVESTIGATION_GOAL:\n"

        f"{goal}"
    )


    try:
        model = get_ops_chat_model()


        agent = create_agent(
            model=model,

            tools=(
                OPS_LANGCHAIN_TOOLS
            ),

            system_prompt=(
                AGENT_SYSTEM_INSTRUCTION
            ),

            middleware=[
                ModelCallLimitMiddleware(
                    run_limit=(
                        MAX_MODEL_CALLS
                    ),

                    exit_behavior="end",
                )
            ],
        )


        result = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=user_prompt
                    )
                ]
            }
        )


        result_messages = (
            result.get("messages")
            or []
        )


        if not result_messages:
            raise LangChainFrameworkAgentError(
                "LangChain agent returned "
                "no messages"
            )


        tool_calls_by_id: dict[
            str,
            dict[str, Any],
        ] = {}


        steps: list[
            AgentToolStepRead
        ] = []


        model_calls_count = 0


        for message in result_messages:
            if isinstance(
                message,
                AIMessage,
            ):
                model_calls_count += 1


                for tool_call in (
                    message.tool_calls
                    or []
                ):
                    tool_call_id = (
                        tool_call.get("id")
                    )

                    if tool_call_id:
                        tool_calls_by_id[
                            tool_call_id
                        ] = tool_call


            elif isinstance(
                message,
                ToolMessage,
            ):
                tool_call = (
                    tool_calls_by_id.get(
                        message.tool_call_id
                    )
                )


                if tool_call is None:
                    continue


                tool_name = (
                    tool_call.get("name")
                )


                tool_arguments = (
                    tool_call.get("args")
                    or {}
                )


                if not tool_name:
                    continue


                if not isinstance(
                    tool_arguments,
                    dict,
                ):
                    tool_arguments = {}


                tool_result = (
                    _normalize_tool_result(
                        message.content
                    )
                )


                steps.append(
                    AgentToolStepRead(
                        iteration=(
                            len(steps) + 1
                        ),

                        tool_name=tool_name,

                        arguments=(
                            tool_arguments
                        ),

                        result=tool_result,
                    )
                )


        final_answer = ""


        for message in reversed(
            result_messages
        ):
            if not isinstance(
                message,
                AIMessage,
            ):
                continue


            if (
                message.tool_calls
                or []
            ):
                continue


            candidate = (
                _get_ai_message_text(
                    message
                )
            )


            if candidate:
                final_answer = candidate
                break


        if not final_answer:
            raise LangChainFrameworkAgentError(
                "LangChain agent returned "
                "no final text answer"
            )


        return (
            LangChainAgentInvestigationRead(
                incident_id=incident_id,

                goal=goal,

                steps=steps,

                tool_calls_count=(
                    len(steps)
                ),

                model_calls_count=(
                    model_calls_count
                ),

                final_answer=(
                    final_answer
                ),

                model_name=(
                    settings.groq_model
                ),

                harness=(
                    "langchain_create_agent"
                ),
            )
        )


    except LangChainFrameworkAgentError:
        raise


    except Exception as exc:
        status_code = _get_status_code(
            exc
        )


        if status_code is not None:
            raise LangChainFrameworkAgentError(
                "LangChain create_agent "
                "request failed "
                f"({status_code}): {exc}"
            ) from exc


        raise LangChainFrameworkAgentError(
            "Unexpected LangChain "
            "create_agent error: "
            f"{type(exc).__name__}: "
            f"{exc}"
        ) from exc