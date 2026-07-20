from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


@pytest.fixture
def client() -> TestClient:
    identity = Identity(uuid4(), uuid4(), "Owner")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("requirements", "requirement_baseline"),
        ("scenarios", "scenario_assessment"),
        ("business-cases", "business_case"),
        ("proposals", "proposal"),
        ("delivery-plans", "delivery_plan"),
    ],
)
def test_business_object_apis_create_list_and_revise(
    client: TestClient, path: str, kind: str
) -> None:
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    collection = f"/api/v1/projects/{project_id}/{path}"
    created = client.post(collection, json={"title": "Draft", "payload": {"a": 1}})

    assert created.status_code == 201
    assert created.json()["kind"] == kind
    assert created.headers["etag"] == '"1"'
    item_id = created.json()["id"]

    revised = client.put(
        f"{collection}/{item_id}",
        headers={"If-Match": '"1"'},
        json={"title": "Revision", "payload": {"a": 2}},
    )
    stale = client.put(
        f"{collection}/{item_id}",
        headers={"If-Match": '"1"'},
        json={"payload": {"a": 3}},
    )

    assert revised.status_code == 200
    assert revised.json()["version"] == 2
    assert revised.headers["etag"] == '"2"'
    assert stale.status_code == 409
    assert [item["id"] for item in client.get(collection).json()] == [item_id]


def test_business_object_update_requires_if_match(client: TestClient) -> None:
    project_id = client.post("/api/v1/projects", json={"name": "Customer"}).json()["id"]
    collection = f"/api/v1/projects/{project_id}/requirements"
    item = client.post(collection, json={"title": "Draft", "payload": {}}).json()

    response = client.put(f"{collection}/{item['id']}", json={"payload": {}})

    assert response.status_code == 422
