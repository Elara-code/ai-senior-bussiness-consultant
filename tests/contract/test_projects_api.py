from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def _client(identity: Identity) -> TestClient:
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def test_project_crud_and_membership_contract() -> None:
    owner = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    client = _client(owner)

    created = client.post("/api/v1/projects", json={"name": "Customer AI"})
    assert created.status_code == 201
    project_id = created.json()["id"]

    listed = client.get("/api/v1/projects")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [project_id]

    updated = client.patch(
        f"/api/v1/projects/{project_id}", json={"stage": "requirements"}
    )
    assert updated.status_code == 200
    assert updated.json()["stage"] == "requirements"

    member_id = uuid4()
    member = client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(member_id), "role": "consultant"},
    )
    assert member.status_code == 201
    assert member.json()["user_id"] == str(member_id)


def test_missing_authentication_is_rejected() -> None:
    response = TestClient(create_app()).get("/api/v1/projects")
    assert response.status_code == 401
