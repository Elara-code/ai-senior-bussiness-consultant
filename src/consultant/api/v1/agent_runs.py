import json
from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from consultant.api.dependencies import AgentRuns, CurrentIdentity
from consultant.domain.agent_runs import AgentKind, AgentRun, AgentRunStatus
from consultant.ports.event_store import RunEvent

router = APIRouter(tags=["agent-runs"])


class AgentRunInput(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    document_version_ids: list[UUID] = Field(default_factory=list)
    confirmed_facts: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class AgentRunOptions(BaseModel):
    language: str = "zh-CN"
    max_steps: int = Field(default=12, ge=1, le=20)
    retrieval_top_k: int = Field(default=8, ge=1, le=20)


class CreateAgentRunRequest(BaseModel):
    agent: AgentKind
    input: AgentRunInput
    options: AgentRunOptions = Field(default_factory=AgentRunOptions)


class AgentRunResponse(BaseModel):
    id: UUID
    project_id: UUID
    agent: AgentKind
    status: AgentRunStatus
    created_at: str
    events_url: str


def _response(run: AgentRun) -> AgentRunResponse:
    return AgentRunResponse(
        id=run.id,
        project_id=run.project_id,
        agent=run.agent_kind,
        status=run.status,
        created_at=run.created_at.isoformat(),
        events_url=f"/api/v1/agent-runs/{run.id}/events",
    )


@router.post(
    "/projects/{project_id}/agent-runs",
    response_model=AgentRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_agent_run(
    project_id: UUID,
    request: CreateAgentRunRequest,
    identity: CurrentIdentity,
    service: AgentRuns,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=255)],
) -> AgentRunResponse:
    run, _ = await service.create(
        identity=identity,
        project_id=project_id,
        agent_kind=request.agent,
        objective=request.input.objective,
        idempotency_key=idempotency_key,
    )
    return _response(run)


@router.get("/agent-runs/{run_id}", response_model=AgentRunResponse)
def get_agent_run(
    run_id: UUID, identity: CurrentIdentity, service: AgentRuns
) -> AgentRunResponse:
    return _response(service.get_visible(identity=identity, run_id=run_id))


@router.post("/agent-runs/{run_id}:cancel", response_model=AgentRunResponse)
async def cancel_agent_run(
    run_id: UUID, identity: CurrentIdentity, service: AgentRuns
) -> AgentRunResponse:
    return _response(await service.cancel(identity=identity, run_id=run_id))


@router.get("/agent-runs/{run_id}/events")
def stream_agent_run_events(
    run_id: UUID,
    identity: CurrentIdentity,
    service: AgentRuns,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    service.get_visible(identity=identity, run_id=run_id)
    after_sequence = int(last_event_id or 0)

    async def generate() -> AsyncIterator[str]:
        async for event in service.events.subscribe(
            run_id=run_id, after_sequence=after_sequence
        ):
            yield _format_sse(event)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(event: RunEvent) -> str:
    data: dict[str, Any] = {
        "run_id": str(event.run_id),
        **event.payload,
        "occurred_at": event.occurred_at.isoformat(),
    }
    return (
        f"id: {event.sequence}\n"
        f"event: {event.event_type}\n"
        f"data: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )
