import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)

from sqlalchemy.dialects.postgresql import (
    UUID,
)

from app.db.base import Base


class IncidentMemory(Base):
    __tablename__ = "incident_memories"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "service_name",
            "memory_hash",
            name=(
                "uq_incident_memories_"
                "workspace_service_hash"
            ),
        ),

        Index(
            "ix_incident_memories_"
            "workspace_service_active",
            "workspace_id",
            "service_name",
            "is_active",
        ),
    )


    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )


    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "incidents.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )


    service_name = Column(
        String(120),
        nullable=False,
        index=True,
    )


    memory_type = Column(
        String(50),
        nullable=False,
        default="operational_pattern",
    )


    summary = Column(
        Text,
        nullable=False,
    )


    evidence = Column(
        Text,
        nullable=False,
    )


    confidence = Column(
        Float,
        nullable=False,
        default=0.7,
    )


    source_thread_id = Column(
        String(255),
        nullable=True,
        index=True,
    )


    source_checkpoint_id = Column(
        String(255),
        nullable=True,
    )


    memory_hash = Column(
        String(64),
        nullable=False,
    )


    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )