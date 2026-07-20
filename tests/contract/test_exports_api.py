from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app


def test_export_api_stores_versioned_draft_file() -> None:
    secret = "export-test-secret"
    identity = Identity(uuid4(), uuid4(), "Owner")
    app = create_app(Settings(environment="test", development_auth_secret=secret))
    client = TestClient(
        app, headers={"Authorization": f"Bearer {encode_development_token(identity, secret)}"}
    )
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    proposal = client.post(
        f"/api/v1/projects/{project_id}/proposals",
        json={"title": "Customer Proposal", "payload": {"scope": "pilot"}},
    ).json()
    response = client.post(
        f"/api/v1/projects/{project_id}/exports",
        json={"item_id": proposal["id"], "format": "docx", "citation_lines": ["[1] source"]},
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "Customer-Proposal-v1.docx"
    assert response.json()["approved"] is False
    assert response.json()["object_key"] in app.state.object_store.objects
