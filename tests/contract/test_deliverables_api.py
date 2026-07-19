from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def test_deliverable_api_preserves_revision_history() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    payload = {
        "kind": "solution_draft",
        "title": "Solution",
        "payload": {"summary": "Draft"},
        "rendered_markdown": "# Solution",
        "source_run_id": str(uuid4()),
        "citations": [],
    }
    created = client.post(f"/api/v1/projects/{project_id}/deliverables", json=payload)
    assert created.status_code == 201
    deliverable_id = created.json()["deliverable"]["id"]

    payload["deliverable_id"] = deliverable_id
    payload["payload"] = {"summary": "Revision 2"}
    updated = client.post(f"/api/v1/projects/{project_id}/deliverables", json=payload)
    history = client.get(f"/api/v1/deliverables/{deliverable_id}/revisions")

    assert updated.status_code == 201
    assert [item["version_number"] for item in history.json()] == [1, 2]
