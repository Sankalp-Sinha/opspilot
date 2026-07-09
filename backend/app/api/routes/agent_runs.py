from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.models.agent_run import (
    AgentRun,
)

from app.schemas.agent_run import (
    AgentRunStatsRead,
)


router = APIRouter()


@router.get(
    "/stats",
    response_model=AgentRunStatsRead,
)
def get_agent_run_stats(
    db: Session = Depends(get_db),
):
    statement = (
        select(
            AgentRun.status,
            func.count(AgentRun.id),
        )
        .group_by(
            AgentRun.status
        )
    )

    rows = db.execute(
        statement
    ).all()


    counts = {
        "queued": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
    }


    for run_status, count in rows:
        if run_status in counts:
            counts[run_status] = int(
                count
            )


    return AgentRunStatsRead(
        total=sum(
            counts.values()
        ),

        queued=counts["queued"],

        running=counts["running"],

        completed=counts["completed"],

        failed=counts["failed"],
    )