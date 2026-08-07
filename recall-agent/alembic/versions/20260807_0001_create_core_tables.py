"""create core tables

Revision ID: 20260807_0001
Revises:
Create Date: 2026-08-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260807_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    reminder_status = postgresql.ENUM(
        "pending", "scheduled", "sent", "skipped", "failed", name="reminder_status"
    )
    agent_log_status = postgresql.ENUM(
        "created", "skipped", "failed", name="agent_log_status"
    )
    reminder_status.create(op.get_bind(), checkfirst=True)
    agent_log_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_businesses_id"), "businesses", ["id"], unique=False)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("preferred_channel", sa.String(length=20), nullable=False),
        sa.Column("is_opted_in", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)

    op.create_table(
        "service_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recommended_interval_days", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_types_id"), "service_types", ["id"], unique=False)

    op.create_table(
        "service_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["service_type_id"], ["service_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_records_id"), "service_records", ["id"], unique=False
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.Column("service_record_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "scheduled",
                "sent",
                "skipped",
                "failed",
                name="reminder_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["service_record_id"], ["service_records.id"]),
        sa.ForeignKeyConstraint(["service_type_id"], ["service_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reminders_id"), "reminders", ["id"], unique=False)

    op.create_table(
        "agent_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("reminder_id", sa.Integer(), nullable=True),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column(
            "decision",
            postgresql.ENUM(
                "created",
                "skipped",
                "failed",
                name="agent_log_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["reminder_id"], ["reminders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_logs_id"), "agent_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_logs_id"), table_name="agent_logs")
    op.drop_table("agent_logs")
    op.drop_index(op.f("ix_reminders_id"), table_name="reminders")
    op.drop_table("reminders")
    op.drop_index(op.f("ix_service_records_id"), table_name="service_records")
    op.drop_table("service_records")
    op.drop_index(op.f("ix_service_types_id"), table_name="service_types")
    op.drop_table("service_types")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")
    op.drop_index(op.f("ix_businesses_id"), table_name="businesses")
    op.drop_table("businesses")

    sa.Enum(name="agent_log_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reminder_status").drop(op.get_bind(), checkfirst=True)
