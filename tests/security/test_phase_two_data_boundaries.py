from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app


def test_project_data_is_not_visible_to_another_organization() -> None:
    secret = "test-development-secret"
    app = create_app(Settings(environment="test", development_auth_secret=secret))
    owner_org, outsider_org = uuid4(), uuid4()

    def token(org_id: UUID) -> str:
        return encode_development_token(
            Identity(organization_id=org_id, user_id=uuid4(), display_name="tester"),
            secret,
        )

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token(owner_org)}"},
            json={"name": "confidential pilot"},
        )
        assert created.status_code == 201
        response = client.get(
            f"/api/v1/projects/{created.json()['id']}",
            headers={"Authorization": f"Bearer {token(outsider_org)}"},
        )
        assert response.status_code == 404
        assert "confidential pilot" not in response.text
