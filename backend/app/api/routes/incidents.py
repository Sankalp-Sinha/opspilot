from uuid import UUID
import traceback
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from app.schemas.agent_investigation import (
    PersistentLangGraphInvestigationRead,
    PersistentLangGraphInvestigationRequest,
    PersistentThreadStateRead,
    PersistentThreadHistoryRead,
    PersistentLangGraphDrainRequest,
    PersistentLangGraphDrainRead,
    PersistentLangGraphResumeRequest,
    PersistentLangGraphResumeRead,
)
from app.services.ai.persistent_langgraph_agent import (
    PersistentLangGraphAgentError,
    investigate_with_persistent_langgraph_agent,
)
from datetime import datetime, timezone
from app.models.agent_run import AgentRun
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.incident import Incident
from app.models.incident_analysis import (
    IncidentAnalysis,
)
from app.schemas.agent_investigation import (
    AgentInvestigationRead,
    AgentInvestigationRequest,
    LangChainAgentInvestigationRead,
    LangGraphAgentInvestigationRead,
)
from app.models.workspace import Workspace
from app.schemas.ai_analysis import (
    IncidentAnalysisRead,
)
from app.services.ai.agent_loop import (
    AgentLoopError,
    investigate_incident_with_agent,
)
from app.schemas.incident import (
    IncidentCreate,
    IncidentRead,
)
from app.services.ai.incident_analyzer import (
    PROMPT_VERSION,
    IncidentAnalysisError,
    analyze_incident_with_ai,
)
from app.schemas.tool_investigation import (
    ToolInvestigationRead,
    ToolInvestigationRequest,
)
from app.services.ai.tool_investigator import (
    ToolInvestigationError,
    investigate_incident_with_one_tool,
)
from app.services.ai.langchain_framework_agent import (
    LangChainFrameworkAgentError,
    investigate_with_langchain_agent,
)
from app.services.ai.langgraph_agent import (
    LangGraphAgentError,
    investigate_with_langgraph_agent,
)
from app.services.ai.langgraph_thread_inspector import (
    LangGraphThreadInspectionError,
    get_persistent_thread_history,
    get_persistent_thread_state,
)

from app.services.ai.persistent_langgraph_recovery import (
    PersistentLangGraphRecoveryError,
    resume_persistent_langgraph_thread,
    start_persistent_langgraph_drained_run,
)


router = APIRouter()


@router.get(
    "",
    response_model=list[IncidentRead],
)
def list_incidents(
    workspace_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    statement = select(Incident)

    if workspace_id is not None:
        statement = statement.where(
            Incident.workspace_id == workspace_id
        )

    statement = statement.order_by(
        Incident.created_at.desc()
    )

    incidents = db.scalars(statement).all()

    return list(incidents)


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
):
    workspace = db.get(
        Workspace,
        payload.workspace_id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    incident = Incident(
        workspace_id=payload.workspace_id,
        title=payload.title,
        description=payload.description,
        service_name=payload.service_name,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


@router.post(
    "/{incident_id}/analyze",
    response_model=IncidentAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
def analyze_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    try:
        ai_output = analyze_incident_with_ai(
            title=incident.title,
            description=incident.description,
            service_name=incident.service_name,
        )

    except IncidentAnalysisError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "AI analysis service failed"
            ),
        ) from exc

    analysis = IncidentAnalysis(
        incident_id=incident.id,
        severity=ai_output.severity,
        category=ai_output.category,
        affected_service=(
            ai_output.affected_service
        ),
        likely_impact=ai_output.likely_impact,
        recommended_next_step=(
            ai_output.recommended_next_step
        ),
        analysis_summary=(
            ai_output.analysis_summary
        ),
        confidence=ai_output.confidence,
        model_name=settings.groq_model,
        prompt_version=PROMPT_VERSION,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


@router.get(
    "/{incident_id}/analyses",
    response_model=list[IncidentAnalysisRead],
)
def list_incident_analyses(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    statement = (
        select(IncidentAnalysis)
        .where(
            IncidentAnalysis.incident_id
            == incident_id
        )
        .order_by(
            IncidentAnalysis.created_at.desc()
        )
    )

    analyses = db.scalars(statement).all()

    return list(analyses)


@router.post(
    "/{incident_id}/tool-investigate",
    response_model=ToolInvestigationRead,
)
def investigate_incident_with_tool(
    incident_id: UUID,

    payload: ToolInvestigationRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    try:
        result = (
            investigate_incident_with_one_tool(
                incident_id=incident.id,

                title=incident.title,

                description=(
                    incident.description
                ),

                service_name=(
                    incident.service_name
                ),

                question=payload.question,
            )
        )

    except ToolInvestigationError as exc:
        print(
            "TOOL INVESTIGATION ERROR:",
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return result

@router.post(
    "/{incident_id}/agent-investigate",
    response_model=AgentInvestigationRead,
)
def run_agent_investigation(
    incident_id: UUID,

    payload: AgentInvestigationRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    agent_run = AgentRun(
        incident_id=incident.id,
        user_goal=payload.goal,
        status="running",
        started_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    try:
        result = (
            investigate_incident_with_agent(
                run_id=agent_run.id,

                incident_id=incident.id,

                title=incident.title,

                description=(
                    incident.description
                ),

                service_name=(
                    incident.service_name
                ),

                goal=payload.goal,
            )
        )

    except AgentLoopError as exc:
        agent_run.status = "failed"

        agent_run.completed_at = (
            datetime.now(timezone.utc)
        )

        db.commit()

        print(
            "AGENT LOOP ERROR:",
            str(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Agent investigation failed"
            ),
        ) from exc

    agent_run.status = "completed"

    agent_run.completed_at = (
        datetime.now(timezone.utc)
    )

    db.commit()

    return result


@router.post(
    "/{incident_id}/langchain-agent-investigate",
    response_model=(
        LangChainAgentInvestigationRead
    ),
)
def run_langchain_agent_investigation(
    incident_id: UUID,

    payload: AgentInvestigationRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )


    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail="Incident not found",
        )


    try:
        return (
            investigate_with_langchain_agent(
                incident_id=incident.id,

                title=incident.title,

                description=(
                    incident.description
                ),

                service_name=(
                    incident.service_name
                ),

                goal=payload.goal,
            )
        )


    except LangChainFrameworkAgentError as exc:
        print(
            "LANGCHAIN FRAMEWORK "
            "AGENT ERROR:",
            str(exc),
        )


        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),

            detail=(
                "LangChain framework "
                "agent investigation failed"
            ),
        ) from exc
    

@router.get(
    "/{incident_id}/persistent-langgraph-threads/{thread_id}/state",

    response_model=(
        PersistentThreadStateRead
    ),
)
def read_persistent_langgraph_thread_state(
    incident_id: UUID,

    thread_id: str,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Incident not found",
        )

    try:
        return get_persistent_thread_state(
            incident_id=incident.id,
            thread_id=thread_id,
        )

    except LangGraphThreadInspectionError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc
    

@router.get(
    "/{incident_id}/persistent-langgraph-threads/{thread_id}/history",

    response_model=(
        PersistentThreadHistoryRead
    ),
)
def read_persistent_langgraph_thread_history(
    incident_id: UUID,

    thread_id: str,

    limit: int = 20,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Incident not found",
        )

    try:
        return get_persistent_thread_history(
            incident_id=incident.id,
            thread_id=thread_id,
            limit=limit,
        )

    except LangGraphThreadInspectionError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc
    

@router.post(
    "/{incident_id}/persistent-langgraph-agent-drain",

    response_model=(
        PersistentLangGraphDrainRead
    ),
)
def drain_persistent_langgraph_investigation(
    incident_id: UUID,

    payload:
        PersistentLangGraphDrainRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Incident not found",
        )

    try:
        return start_persistent_langgraph_drained_run(
            incident_id=incident.id,

            title=incident.title,

            description=(
                incident.description
            ),

            service_name=(
                incident.service_name
            ),

            goal=payload.goal,

            thread_id=(
                payload.thread_id
            ),
        )

    except PersistentLangGraphRecoveryError as exc:
        print(
            "PERSISTENT LANGGRAPH "
            "DRAIN ERROR:",
            str(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Persistent LangGraph "
                "drain failed"
            ),
        ) from exc
    

@router.post(
    "/{incident_id}/persistent-langgraph-agent-resume",

    response_model=(
        PersistentLangGraphResumeRead
    ),
)
def resume_persistent_langgraph_investigation(
    incident_id: UUID,

    payload:
        PersistentLangGraphResumeRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Incident not found",
        )

    try:
        return resume_persistent_langgraph_thread(
            incident_id=incident.id,

            thread_id=(
                payload.thread_id
            ),
        )

    except PersistentLangGraphRecoveryError as exc:
        print(
            "PERSISTENT LANGGRAPH "
            "RESUME ERROR:",
            str(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Persistent LangGraph "
                "resume failed"
            ),
        ) from exc

@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident

@router.post(
    "/{incident_id}/langgraph-agent-investigate",

    response_model=(
        LangGraphAgentInvestigationRead
    ),
)
def run_langgraph_agent_investigation(
    incident_id: UUID,

    payload: AgentInvestigationRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )


    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail="Incident not found",
        )


    try:
        return (
            investigate_with_langgraph_agent(
                incident_id=incident.id,

                title=incident.title,

                description=(
                    incident.description
                ),

                service_name=(
                    incident.service_name
                ),

                goal=payload.goal,
            )
        )


    except LangGraphAgentError as exc:
        print("\nLANGGRAPH AGENT ERROR:")
        traceback.print_exception(
            type(exc),
            exc,
            exc.__traceback__,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "LangGraph agent "
                "investigation failed"
            ),
        ) from exc


@router.post(
    "/{incident_id}/persistent-langgraph-agent-investigate",

    response_model=(
        PersistentLangGraphInvestigationRead
    ),
)
def run_persistent_langgraph_investigation(
    incident_id: UUID,

    payload:
        PersistentLangGraphInvestigationRequest,

    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )


    if incident is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail="Incident not found",
        )


    try:
        return (
            investigate_with_persistent_langgraph_agent(
                incident_id=incident.id,

                title=incident.title,

                description=(
                    incident.description
                ),

                service_name=(
                    incident.service_name
                ),

                goal=payload.goal,

                thread_id=(
                    payload.thread_id
                ),
            )
        )


    except PersistentLangGraphAgentError as exc:
        print(
            "PERSISTENT LANGGRAPH "
            "AGENT ERROR:",
            str(exc),
        )


        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),

            detail=(
                "Persistent LangGraph "
                "investigation failed"
            ),
        ) from exc