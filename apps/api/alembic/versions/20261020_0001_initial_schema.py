"""initial schema for credit cabinet persistence

Revision ID: 20261020_0001
Revises:
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261020_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("synthetic_name", sa.String(255), nullable=False),
        sa.Column("synthetic_registration_id", sa.String(32), nullable=False),
        sa.Column("scenario_key", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_companies_synthetic_registration_id", "companies", ["synthetic_registration_id"], unique=True)
    op.create_index("ix_companies_scenario_key", "companies", ["scenario_key"])

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("min_amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("max_amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("min_term_months", sa.Integer(), nullable=False),
        sa.Column("max_term_months", sa.Integer(), nullable=False),
        sa.Column("rules_version", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
    )
    op.create_index("ix_products_code", "products", ["code"], unique=True)

    user_role = sa.Enum("customer", "bank", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("demo_login", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_demo_login", "users", ["demo_login"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    app_state = sa.Enum(
        "DRAFT",
        "SUBMITTED",
        "VALIDATING",
        "NEEDS_INFO",
        "SCORING",
        "UNDER_REVIEW",
        "APPROVED",
        "REJECTED",
        "ACCEPTED",
        "SIGNED_SIMULATED",
        "DISBURSED_SIMULATED",
        name="application_state",
    )
    app_state.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("amount_minor", sa.BigInteger()),
        sa.Column("currency", sa.String(3), server_default="RUB"),
        sa.Column("term_months", sa.Integer()),
        sa.Column("purpose", sa.Text()),
        sa.Column("state", app_state, nullable=False),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("clarification_request", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_applications_company_id", "applications", ["company_id"])
    op.create_index("ix_applications_state", "applications", ["state"])

    for table, cols in [
        (
            "financial_snapshots",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
                sa.Column("revenue_minor", sa.BigInteger()),
                sa.Column("expenses_minor", sa.BigInteger()),
                sa.Column("liabilities_minor", sa.BigInteger()),
                sa.Column("captured_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "documents",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
                sa.Column("kind", sa.String(64), nullable=False),
                sa.Column("storage_key", sa.String(512), nullable=False),
                sa.Column("content_hash", sa.String(128), nullable=False),
                sa.Column("synthetic", sa.Boolean(), server_default=sa.text("true")),
                sa.Column("created_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "check_results",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
                sa.Column("source", sa.String(64), nullable=False),
                sa.Column("mock_version", sa.String(64), nullable=False),
                sa.Column("result", sa.JSON(), nullable=False),
                sa.Column("checked_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "risk_assessments",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
                sa.Column("score", sa.Integer(), nullable=False),
                sa.Column("factors", sa.JSON(), nullable=False),
                sa.Column("model_version", sa.String(64), nullable=False),
                sa.Column("created_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "decisions",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
                sa.Column("outcome", sa.String(64), nullable=False),
                sa.Column("reason_codes", sa.JSON(), nullable=False),
                sa.Column("offered_terms", sa.JSON(), nullable=False),
                sa.Column("rules_version", sa.String(64), nullable=False),
                sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
                sa.Column("created_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "application_events",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
                sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
                sa.Column("old_state", sa.String(64)),
                sa.Column("new_state", sa.String(64)),
                sa.Column("action", sa.String(64), nullable=False),
                sa.Column("correlation_id", sa.String(64)),
                sa.Column("payload", sa.JSON(), nullable=False),
                sa.Column("occurred_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "idempotency_records",
            [
                sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("route", sa.String(128), nullable=False),
                sa.Column("key", sa.String(128), nullable=False),
                sa.Column("request_hash", sa.String(128), nullable=False),
                sa.Column("response", sa.JSON(), nullable=False),
                sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
                sa.UniqueConstraint("actor_id", "route", "key", name="uq_idempotency"),
            ],
        ),
    ]:
        op.create_table(table, *cols)
        if table != "idempotency_records":
            op.create_index(f"ix_{table}_application_id", table, ["application_id"])


def downgrade() -> None:
    for table in [
        "idempotency_records",
        "application_events",
        "decisions",
        "risk_assessments",
        "check_results",
        "documents",
        "financial_snapshots",
        "applications",
        "users",
        "products",
        "companies",
    ]:
        op.drop_table(table)
    sa.Enum(name="application_state").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
