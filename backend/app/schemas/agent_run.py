from pydantic import BaseModel


class AgentRunStatsRead(BaseModel):
    total: int

    queued: int

    running: int

    completed: int

    failed: int