"""link decisions to financial snapshot; product catalog extras

Revision ID: 20261020_0004
Revises: 20261020_0003
Create Date: 2026-10-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261020_0004"
down_revision = "20261020_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "decisions",
        sa.Column(
            "financial_snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("financial_snapshots.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "decisions",
        sa.Column("product_code", sa.String(64), nullable=True),
    )
    op.add_column(
        "decisions",
        sa.Column("application_version", sa.Integer(), nullable=True),
    )
    # Catalog fields used by data/products.json (single source loaded into ORM)
    op.add_column("products", sa.Column("demo_rate_annual", sa.Float(), nullable=True))
    op.add_column("products", sa.Column("product_version", sa.String(64), nullable=True))
    op.add_column("products", sa.Column("allowed_goals", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("required_fields", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("fit_note", sa.Text(), nullable=True))
    op.add_column(
        "financial_snapshots",
        sa.Column("debt_service_monthly_minor", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "financial_snapshots",
        sa.Column("period_label", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_snapshots", "period_label")
    op.drop_column("financial_snapshots", "debt_service_monthly_minor")
    op.drop_column("products", "fit_note")
    op.drop_column("products", "required_fields")
    op.drop_column("products", "allowed_goals")
    op.drop_column("products", "product_version")
    op.drop_column("products", "demo_rate_annual")
    op.drop_column("decisions", "application_version")
    op.drop_column("decisions", "product_code")
    op.drop_column("decisions", "financial_snapshot_id")
