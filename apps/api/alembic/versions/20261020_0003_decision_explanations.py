"""add decision explanation columns for open-weight LLM narration

Revision ID: 20261020_0003
Revises: 20261020_0002
Create Date: 2026-10-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261020_0003"
down_revision = "20261020_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("decisions", sa.Column("explanation_client", sa.Text(), nullable=True))
    op.add_column("decisions", sa.Column("explanation_bank", sa.Text(), nullable=True))
    op.add_column(
        "decisions",
        sa.Column("llm_meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )


def downgrade() -> None:
    op.drop_column("decisions", "llm_meta")
    op.drop_column("decisions", "explanation_bank")
    op.drop_column("decisions", "explanation_client")
