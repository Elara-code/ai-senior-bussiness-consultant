from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app


def test_approval_api_uses_server_snapshot_and_updates_target_status() -> None:
    secret = "approval-test-secret"
    identity = Identity(uuid4(), uuid4(), "Owner")
    app = create_app(Settings(environment="test", development_auth_secret=secret))
    client = TestClient(
        app,
        headers={"Authorization": f"Bearer {encode_development_token(identity, secret)}"},
    )
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    proposal_url = f"/api/v1/projects/{project_id}/proposals"
    proposal = client.post(
        proposal_url, json={"title": "Proposal", "payload": {"scope": "approved"}}
    ).json()

    submitted = client.post(
        f"/api/v1/projects/{project_id}/approvals",
        json={
            "target_kind": "proposal",
            "target_id": proposal["id"],
            "target_version": 1,
        },
    )
    decided = client.post(
        f"/api/v1/projects/{project_id}/approvals/{submitted.json()['id']}/decision",
        json={
            "decision": "approved",
            "expected_target_version": 1,
            "comment": "同意",
        },
    )
    target = client.get(f"{proposal_url}/{proposal['id']}")

    assert submitted.status_code == 201
    assert submitted.json()["snapshot"]["payload"] == {"scope": "approved"}
    assert decided.status_code == 200
    assert decided.json()["decision"] == "approved"
    assert target.json()["status"] == "approved"
