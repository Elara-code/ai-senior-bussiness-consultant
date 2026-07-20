import asyncio
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def test_sse_supports_event_ids_and_terminal_close() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    created = client.post(
        f"/api/v1/projects/{project_id}/agent-runs",
        headers={"Idempotency-Key": "request-0001"},
        json={
            "agent": "requirement_analysis",
            "input": {"objective": "Analyze"},
        },
    )
    run_id = UUID(created.json()["id"])

    async def runner(run: object) -> dict[str, str]:
        del run
        return {"result": "ok"}

    asyncio.run(app.state.agent_run_service.execute(run_id=run_id, runner=runner))
    response = client.get(f"/api/v1/agent-runs/{run_id}/events")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "id: 1" in response.text
    assert "event: run.started" in response.text
    assert "id: 2" in response.text
    assert "event: run.completed" in response.text

    resumed = client.get(
        f"/api/v1/agent-runs/{run_id}/events", headers={"Last-Event-ID": "1"}
    )
    assert "id: 1" not in resumed.text
    assert "id: 2" in resumed.text


def test_only_failed_runs_can_be_retried() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    run = client.post(
        f"/api/v1/projects/{project_id}/agent-runs",
        headers={"Idempotency-Key": "retry-request-01"},
        json={"agent": "requirement_analysis", "input": {"objective": "Analyze"}},
    ).json()
    response = client.post(f"/api/v1/agent-runs/{run['id']}:retry")
    assert response.status_code == 409
