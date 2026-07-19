from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def test_upload_document_returns_pending_version() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("interview.md", b"manual reporting", "text/markdown")},
    )

    assert response.status_code == 202
    assert response.json()["filename"] == "interview.md"
    assert response.json()["status"] == "pending"


def test_upload_rejects_unsupported_content_type() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("payload.exe", b"unsafe", "application/octet-stream")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"
