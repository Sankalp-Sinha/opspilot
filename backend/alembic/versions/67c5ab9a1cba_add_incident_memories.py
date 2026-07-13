"""add incident memories

Revision ID: 67c5ab9a1cba
Revises: f3fd1f35f0fc
Create Date: 2026-07-13 23:07:11.967236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '67c5ab9a1cba'
down_revision: Union[str, Sequence[str], None] = 'f3fd1f35f0fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident_memories",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),

        sa.Column(
            "service_name",
            sa.String(length=120),
            nullable=False,
        ),

        sa.Column(
            "memory_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "evidence",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "source_thread_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "source_checkpoint_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "memory_hash",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "workspace_id",
            "service_name",
            "memory_hash",
            name=(
                "uq_incident_memories_"
                "workspace_service_hash"
            ),
        ),
    )


    op.create_index(
        op.f(
            "ix_incident_memories_workspace_id"
        ),
        "incident_memories",
        ["workspace_id"],
        unique=False,
    )


    op.create_index(
        op.f(
            "ix_incident_memories_incident_id"
        ),
        "incident_memories",
        ["incident_id"],
        unique=False,
    )


    op.create_index(
        op.f(
            "ix_incident_memories_service_name"
        ),
        "incident_memories",
        ["service_name"],
        unique=False,
    )


    op.create_index(
        op.f(
            "ix_incident_memories_"
            "source_thread_id"
        ),
        "incident_memories",
        ["source_thread_id"],
        unique=False,
    )


    op.create_index(
        "ix_incident_memories_"
        "workspace_service_active",
        "incident_memories",
        [
            "workspace_id",
            "service_name",
            "is_active",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_incident_memories_"
        "workspace_service_active",
        table_name="incident_memories",
    )

    op.drop_index(
        op.f(
            "ix_incident_memories_"
            "source_thread_id"
        ),
        table_name="incident_memories",
    )

    op.drop_index(
        op.f(
            "ix_incident_memories_"
            "service_name"
        ),
        table_name="incident_memories",
    )

    op.drop_index(
        op.f(
            "ix_incident_memories_"
            "incident_id"
        ),
        table_name="incident_memories",
    )

    op.drop_index(
        op.f(
            "ix_incident_memories_"
            "workspace_id"
        ),
        table_name="incident_memories",
    )

    op.drop_table("incident_memories")
