from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def test_demo_flow_from_project_to_completed_agent_run() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    app = create_app(
        Settings(
            environment="test",
            development_auth_secret=SECRET,
            auto_execute_jobs=True,
        )
    )
    token = encode_development_token(identity, SECRET)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})

    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    uploaded = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={
            "file": (
                "interview.md",
                "# 当前流程\n\n每周经营报告由三名员工手工汇总。".encode(),
                "text/markdown",
            )
        },
    )
    assert uploaded.status_code == 202
    documents = client.get(f"/api/v1/projects/{project_id}/documents").json()
    assert documents[0]["status"] == "ready"

    retrieval = client.post(
        f"/api/v1/projects/{project_id}/retrieval:search",
        json={"query": "经营报告如何汇总？"},
    )
    assert retrieval.status_code == 200
    assert retrieval.json()["hits"]

    created = client.post(
        f"/api/v1/projects/{project_id}/agent-runs",
        headers={"Idempotency-Key": "e2e-request-0001"},
        json={
            "agent": "requirement_analysis",
            "input": {"objective": "分析经营报告现状"},
        },
    )
    run_id = UUID(created.json()["id"])
    run = client.get(f"/api/v1/agent-runs/{run_id}")
    events = client.get(f"/api/v1/agent-runs/{run_id}/events")

    assert run.json()["status"] == "completed"
    assert "event: run.started" in events.text
    assert "event: run.completed" in events.text
