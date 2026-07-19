from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def _headers(identity: Identity) -> dict[str, str]:
    token = encode_development_token(identity, SECRET)
    return {"Authorization": f"Bearer {token}"}


def test_non_member_gets_not_found_instead_of_resource_disclosure() -> None:
    organization_id = uuid4()
    owner = Identity(organization_id=organization_id, user_id=uuid4(), display_name="Owner")
    outsider = Identity(
        organization_id=organization_id, user_id=uuid4(), display_name="Outsider"
    )
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    client = TestClient(app)

    created = client.post(
        "/api/v1/projects", json={"name": "Secret"}, headers=_headers(owner)
    )
    project_id = created.json()["id"]
    response = client.get(f"/api/v1/projects/{project_id}", headers=_headers(outsider))

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_tampered_development_token_is_rejected() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="User")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)

    response = TestClient(app).get(
        "/api/v1/projects", headers={"Authorization": f"Bearer {token}changed"}
    )

    assert response.status_code == 401
