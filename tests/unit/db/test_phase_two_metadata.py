from sqlalchemy import JSON, UniqueConstraint

from consultant.adapters.db import models  # noqa: F401
from consultant.adapters.db.base import Base


def test_phase_two_metadata_contains_business_loop_tables() -> None:
    required = {
        "requirement_baselines",
        "scenario_assessments",
        "business_cases",
        "proposals",
        "delivery_plans",
        "knowledge_candidates",
        "approvals",
        "workflow_executions",
        "business_object_dependencies",
    }
    assert required <= set(Base.metadata.tables)


def test_business_tables_have_version_and_project_scope() -> None:
    table = Base.metadata.tables["requirement_baselines"]
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("organization_id", "project_id", "id", "version") in unique_columns
    assert {"organization_id", "project_id", "version", "payload"} <= {
        column.name for column in table.columns
    }


def test_approval_snapshot_uses_json_type() -> None:
    snapshot = Base.metadata.tables["approvals"].columns["snapshot"]
    assert isinstance(snapshot.type, JSON)
