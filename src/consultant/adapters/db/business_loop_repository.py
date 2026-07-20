from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from consultant.adapters.db.models import (
    BusinessCaseRow,
    DeliveryPlanRow,
    KnowledgeCandidateRow,
    ProposalRow,
    RequirementBaselineRow,
    ScenarioAssessmentRow,
)
from consultant.domain.business_loop import BusinessObjectKind, VersionedBusinessObject

RowType = type[
    RequirementBaselineRow
    | ScenarioAssessmentRow
    | BusinessCaseRow
    | ProposalRow
    | DeliveryPlanRow
    | KnowledgeCandidateRow
]

ROWS: dict[BusinessObjectKind, RowType] = {
    BusinessObjectKind.REQUIREMENT_BASELINE: RequirementBaselineRow,
    BusinessObjectKind.SCENARIO_ASSESSMENT: ScenarioAssessmentRow,
    BusinessObjectKind.BUSINESS_CASE: BusinessCaseRow,
    BusinessObjectKind.PROPOSAL: ProposalRow,
    BusinessObjectKind.DELIVERY_PLAN: DeliveryPlanRow,
    BusinessObjectKind.KNOWLEDGE_CANDIDATE: KnowledgeCandidateRow,
}


class SqlAlchemyBusinessObjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: VersionedBusinessObject) -> None:
        row_type = ROWS[item.kind]
        values = dict(
            row_id=UUID(int=(item.id.int + item.version) % (1 << 128)),
            id=item.id,
            organization_id=item.organization_id,
            project_id=item.project_id,
            title=item.title,
            version=item.version,
            status=item.status.value,
            payload=item.payload,
            statements=[statement.model_dump(mode="json") for statement in item.statements],
            stale=item.stale,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        self._session.add(row_type(**values))

    async def get_latest(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        item_id: UUID,
    ) -> VersionedBusinessObject | None:
        for kind, row_type in ROWS.items():
            statement = (
                select(row_type)
                .where(
                    row_type.organization_id == organization_id,
                    row_type.project_id == project_id,
                    row_type.id == item_id,
                )
                .order_by(row_type.version.desc())
                .limit(1)
            )
            row = await self._session.scalar(statement)
            if row is not None:
                return self._to_domain(row, kind)
        return None

    async def list_latest(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        kind: BusinessObjectKind | None = None,
    ) -> Sequence[VersionedBusinessObject]:
        kinds = [kind] if kind is not None else list(ROWS)
        latest: dict[UUID, VersionedBusinessObject] = {}
        for current_kind in kinds:
            row_type = ROWS[current_kind]
            rows = (
                await self._session.scalars(
                    select(row_type).where(
                        row_type.organization_id == organization_id,
                        row_type.project_id == project_id,
                    )
                )
            ).all()
            for row in rows:
                item = self._to_domain(row, current_kind)
                if item.id not in latest or item.version > latest[item.id].version:
                    latest[item.id] = item
        return sorted(latest.values(), key=lambda item: item.updated_at, reverse=True)

    async def mark_stale(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        item_ids: set[UUID],
    ) -> None:
        for row_type in ROWS.values():
            await self._session.execute(
                update(row_type)
                .where(
                    row_type.organization_id == organization_id,
                    row_type.project_id == project_id,
                    row_type.id.in_(item_ids),
                )
                .values(stale=True)
            )

    @staticmethod
    def _to_domain(row: Any, kind: BusinessObjectKind) -> VersionedBusinessObject:
        return VersionedBusinessObject(
            id=row.id,
            organization_id=row.organization_id,
            project_id=row.project_id,
            kind=kind,
            title=row.title,
            payload=row.payload,
            statements=row.statements,
            version=row.version,
            status=row.status,
            stale=row.stale,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
