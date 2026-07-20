"""Add phase two business loop schema."""

from collections.abc import Sequence

from alembic import op

from consultant.adapters.db import models  # noqa: F401
from consultant.adapters.db.base import Base

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE_NAMES = (
    "requirement_baselines",
    "scenario_assessments",
    "business_cases",
    "proposals",
    "delivery_plans",
    "knowledge_candidates",
    "approvals",
    "workflow_executions",
)


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(
        bind=bind,
        tables=[Base.metadata.tables[name] for name in TABLE_NAMES],
        checkfirst=True,
    )


def downgrade() -> None:
    for name in reversed(TABLE_NAMES):
        op.drop_table(name)
