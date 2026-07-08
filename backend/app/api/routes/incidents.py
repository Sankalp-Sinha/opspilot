from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.incident import Incident
from app.models.incident_analysis import (
    IncidentAnalysis,
)
from app.models.workspace import Workspace
from app.schemas.ai_analysis import (
    IncidentAnalysisRead,
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
        model_name=settings.gemini_model,
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