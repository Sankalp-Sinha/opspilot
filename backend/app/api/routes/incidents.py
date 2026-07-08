from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.incident import Incident
from app.models.workspace import Workspace
from app.schemas.incident import (
    IncidentCreate,
    IncidentRead,
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