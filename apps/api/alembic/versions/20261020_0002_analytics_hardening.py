"""add ALTERNATIVE/CHECK_UNAVAILABLE states and decision.metrics

Revision ID: 20261020_0002
Revises: 20261020_0001
Create Date: 2026-10-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261020_0002"
down_revision: Union[str, None] = "20261020_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE application_state ADD VALUE IF NOT EXISTS 'ALTERNATIVE'")
    op.execute("ALTER TYPE application_state ADD VALUE IF NOT EXISTS 'CHECK_UNAVAILABLE'")
    op.add_column("decisions", sa.Column("metrics", sa.JSON(), nullable=True))
    op.execute("UPDATE decisions SET metrics = '{}'::json WHERE metrics IS NULL")


def downgrade() -> None:
    op.drop_column("decisions", "metrics")
    # Postgres cannot easily remove enum values; leave type widened.
