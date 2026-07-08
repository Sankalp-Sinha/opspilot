from fastapi import APIRouter

from app.api.routes import (
    health,
    incidents,
    workspaces,
)


api_router = APIRouter()


api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    workspaces.router,
    prefix="/api/v1/workspaces",
    tags=["Workspaces"],
)

api_router.include_router(
    incidents.router,
    prefix="/api/v1/incidents",
    tags=["Incidents"],
)