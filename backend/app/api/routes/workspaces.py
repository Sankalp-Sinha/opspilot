from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceRead,
)


router = APIRouter()


@router.post(
    "",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
):
    existing_workspace = db.scalar(
        select(Workspace).where(
            Workspace.slug == payload.slug
        )
    )

    if existing_workspace:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workspace slug already exists",
        )

    workspace = Workspace(
        name=payload.name,
        slug=payload.slug,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace